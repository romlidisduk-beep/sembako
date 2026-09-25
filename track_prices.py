
    Sites like Panel Harga Bapanas and PIHPS render heavily with
    JavaScript, so a plain HTTP fetch sometimes only returns a shell
    page with no figures. This never raises; an empty result just means
    "coba lagi nanti / cek manual", which the caller turns into a
    human-readable placeholder rather than failing the whole run.
    """
    return re.findall(r"Rp\.?\s*([0-9][0-9.,]*)", text)[:limit]


def extract_bps_press_release_title(text: str) -> str | None:
    """Pull the title of a BPS press release about NTP/harga gabah, if present.

    BPS kabupaten sites repost the monthly "Nilai Tukar Petani ... harga
    gabah" provincial release. This looks for the Indonesian or English
    title pattern in raw (or lightly cleaned) HTML/text.
    """
    match = re.search(
        r"(Nilai Tukar Petani[^<\"\n]{0,160}|Farmer Exchange Rate[^<\"\n]{0,160})",
        text,
    )
    return match.group(1).strip() if match else None


def fetch_bps_kabupaten_reference(base_url: str) -> str:
    """Monthly validator: latest NTP/harga-gabah release title from a BPS
    kabupaten site, or a 'cek manual' pointer if it can't be parsed.
    """
    url = f"{base_url}/en/pressrelease"
    try:
        text = fetch_text(url, accept="text/html")
    except RuntimeError:
        return f"Cek manual: {url}"
    title = extract_bps_press_release_title(text)
    return title or f"Tidak terbaca otomatis - cek manual: {url}"


def fetch_national_reference_prices(
    date: str,
    hpp_kdmp: int = HPP_KDMP_DEFAULT,
    pengepul_manual: str = "",
) -> dict[str, Any]:
    """Kumpulkan referensi gabah/beras nasional & daerah di luar SISKAPERBAPO.

    Selalu mengembalikan dict lengkap (tidak pernah raise) — setiap sumber
    yang gagal diambil hanya diisi keterangan gagal, supaya satu sumber
    yang down tidak menggagalkan seluruh laporan harian.
    """
    result: dict[str, Any] = {"date": date}

    try:
        text = fetch_text(NATIONAL_REFERENCE_URLS["panelBapanas"], accept="text/html")
        figures = extract_rupiah_figures(text)
        result["panelBapanas"] = ",".join(figures) if figures else "Data tidak ditemukan di halaman"
    except RuntimeError as error:
        result["panelBapanas"] = f"Gagal diambil: {error}"

    try:
        text = fetch_text(NATIONAL_REFERENCE_URLS["pihps"], accept="text/html")
        figures = extract_rupiah_figures(text)
        result["pihps"] = ",".join(figures) if figures else "Data tidak ditemukan di halaman"
    except RuntimeError as error:
        result["pihps"] = f"Gagal diambil: {error}"

    # Rilis BPS kabupaten bulanan — cukup dicek awal bulan, hemat request
    # di hari-hari lain karena rilisnya memang bulanan, bukan harian.
    day = int(date.split("-")[2]) if valid_date(date) else datetime.now().day
    if day <= 5:
        result["bpsGresik"] = fetch_bps_kabupaten_reference(BPS_KABUPATEN_URLS["gresik"])
        result["bpsLamongan"] = fetch_bps_kabupaten_reference(BPS_KABUPATEN_URLS["lamongan"])
    else:
        result["bpsGresik"] = "(belum waktunya cek - rilis BPS bulanan)"
        result["bpsLamongan"] = "(belum waktunya cek - rilis BPS bulanan)"

    result["hppKdmp"] = hpp_kdmp
    result["pengepulManual"] = pengepul_manual
    result["pengepulNote"] = (
        "Tidak ada sumber publik untuk harga pengepul/tengkulak — isi manual "
        "kalau sudah dicek sendiri (mis. lewat telepon/WA)."
    )
    return result


def append_national_reference_history(path: Path, entry: dict[str, Any]) -> None:
    row = {field: entry.get(field, "") for field in NATIONAL_CSV_FIELDS}
    is_new = not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=NATIONAL_CSV_FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow(row)


def package_quantity(size: str | None, unit: str | None) -> float:
    """Return the package quantity in the record's declared unit.

    A retail price is the total price for ``size``.  Market records use
    ``1 kg``/``1 liter`` and therefore naturally remain unchanged.
    Unknown package formats are deliberately treated as one unit rather than
    guessed, so the comparison never invents a conversion.
    """
    if not size:
        return 1.0
    match = SIZE_PATTERN.match(str(size))
    if not match:
        return 1.0
    quantity = float(match.group("quantity").replace(",", "."))
    source_unit = UNIT_ALIASES.get(match.group("unit").lower(), match.group("unit").lower())
    target_unit = (unit or "").strip().lower()
    if target_unit in {"kilogram", "gram"}:
        target_unit = UNIT_ALIASES[target_unit]
    if target_unit in {"l", "litre"}:
        target_unit = "liter"
    if source_unit == "g" and target_unit == "kg":
        return quantity / 1000
    if source_unit == "ml" and target_unit == "liter":
        return quantity / 1000
    if source_unit != target_unit:
        return 1.0
    return quantity if quantity > 0 else 1.0


def comparison_price(record: dict[str, Any]) -> float:
    """Return a comparable price for one declared unit."""
    try:
        price = float(record.get("price", 0))
    except (TypeError, ValueError):
        return 0.0
    quantity = package_quantity(record.get("size"), record.get("unit"))
    return price / quantity if quantity > 0 else price


def price_description(record: dict[str, Any]) -> str:
    price = currency(float(record["price"]))
    unit = record.get("unit") or "unit"
    quantity = package_quantity(record.get("size"), unit)
    if quantity != 1:
        size = record.get("size") or f"{quantity:g} {unit}"
        return f"{price}/{size} (≈{currency(comparison_price(record))}/{unit})"
    return f"{price}/{unit}"


def read_csv_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            try:
                area = (row.get("area") or "").strip().lower()
                source_type = (row.get("sourceType") or "toko").strip().lower()
                commodity_key = (row.get("commodityKey") or "").strip().lower()
                date = (row.get("date") or "").strip()
                location = (row.get("location") or "").strip()
                price = float(str(row.get("price", "")).strip().replace("Rp", "").replace(".", ""))
                if (
                    not valid_date(date)
                    or area not in AREAS
                    or source_type not in SOURCE_TYPES - {"pasar rakyat"}
                    or commodity_key not in COMMODITY_BY_KEY
                    or not location
                    or not math.isfinite(price)
                    or price <= 0
                    or not price.is_integer()
                ):
                    continue
                commodity = COMMODITY_BY_KEY[commodity_key]
                records.append(
                    {
                        "date": date,
                        "area": area,
                        "marketId": (row.get("marketId") or f"retail:{location}").strip(),
                        "location": location,
                        "sourceType": source_type,
                        "commodityKey": commodity_key,
                        "commodity": (row.get("commodity") or commodity.label).strip(),
                        "brand": (row.get("brand") or "").strip(),
                        "productName": (
                            row.get("productName")
                            or row.get("commodity")
                            or commodity.label
                        ).strip(),
                        "size": (row.get("size") or "").strip(),
                        "unit": (row.get("unit") or commodity.unit).strip().lower(),
                        "price": int(price),
                        "priceType": (row.get("priceType") or "normal").strip().lower(),
                        "stockStatus": (row.get("stockStatus") or "perlu dikonfirmasi").strip(),
                        "confidence": (row.get("confidence") or "input-manual").strip(),
                        "observedAt": (row.get("observedAt") or date).strip(),
                        "address": (row.get("address") or "").strip(),
                        "sourceUrl": (row.get("sourceUrl") or "").strip(),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    return records


def write_csv_records(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(records)


def merge_history(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for record in [*existing, *incoming]:
        key = "|".join(
            [
                str(record["date"]),
                str(record["area"]),
                str(record["marketId"]),
                str(record["commodityKey"]),
                str(record["sourceType"]),
            ]
        )
        merged[key] = record
    return sorted(
        merged.values(),
        key=lambda record: (
            record["date"],
            record["area"],
            record["commodityKey"],
            record["location"],
        ),
    )


def daily_averages(
    history: list[dict[str, Any]],
    area: str,
    commodity_key: str,
    before_date: str,
) -> list[tuple[str, float]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for record in history:
        if (
            record["area"] == area
            and record["commodityKey"] == commodity_key
            and record["sourceType"] == "pasar rakyat"
            and record["date"] < before_date
        ):
            grouped[record["date"]].append(float(record["price"]))
    return sorted(
        (date, sum(values) / len(values))
        for date, values in grouped.items()
        if values
    )


def average(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def trend_signal(
    history: list[dict[str, Any]],
    date: str,
    area: str,
    commodity: Commodity,
    latest_records: list[dict[str, Any]],
) -> dict[str, Any]:
    latest_price = average([comparison_price(record) for record in latest_records])
    previous_days = daily_averages(history, area, commodity.key, date)
    base = {
        "area": area,
        "commodityKey": commodity.key,
        "commodity": commodity.label,
        "unit": commodity.unit,
        "latestPrice": latest_price,
    }
    if latest_price is None:
        return {
            **base,
            "previousAverage": None,
            "changePercent": None,
            "signal": "TIDAK ADA DATA",
            "reason": "Komoditas tidak berhasil dibaca pada tanggal laporan.",
        }
    if len(previous_days) < 2:
        return {
            **base,
            "previousAverage": None,
            "changePercent": None,
            "signal": "BASELINE",
            "reason": "Belum ada riwayat minimal dua hari untuk membaca tren.",
        }

    recent = previous_days[-7:]
    previous_average = average([value for _, value in recent]) or 0
    change_percent = ((latest_price - previous_average) / previous_average * 100) if previous_average else 0
    last_three = [value for _, value in previous_days[-3:]]
    last_dates = [datetime.strptime(day, "%Y-%m-%d") for day, _ in previous_days[-3:]]
    latest_day = datetime.strptime(date, "%Y-%m-%d")
    rising_three_days = (
        len(last_three) == 3
        and last_dates[1] - last_dates[0] == timedelta(days=1)
        and last_dates[2] - last_dates[1] == timedelta(days=1)
        and latest_day - last_dates[-1] == timedelta(days=1)
        and last_three[0] < last_three[1] < last_three[2] < latest_price
    )
    historical_low = min(value for _, value in previous_days)

    if rising_three_days or change_percent >= 2:
        reason = (
            "Rata-rata pasar naik setidaknya tiga hari berturut-turut."
            if rising_three_days
            else "Harga terbaru minimal 2% di atas rata-rata tujuh hari."
        )
        signal = "WASPADA NAIK"
    elif latest_price <= historical_low * 1.01:
        reason = "Harga dekat titik terendah pada riwayat yang tersimpan."
        signal = "MURAH"
    else:
        reason = "Belum ada sinyal kenaikan kuat atau titik murah baru."
        signal = "NORMAL"

    return {
        **base,
        "previousAverage": previous_average,
        "changePercent": change_percent,
        "signal": signal,
        "reason": reason,
    }


def currency(value: float) -> str:
    return f"Rp{round(value):,}".replace(",", ".")


def build_telegram_messages(
    records: list[dict[str, Any]],
    date: str,
    limit: int = 40,
    max_length: int = 3900,
) -> list[str]:
    """Build chat-safe messages ordered from the cheapest price.

    Used for both Telegram (max_length long, one bot API call per message)
    and WhatsApp via CallMeBot (max_length short — see WHATSAPP_MAX_MESSAGE_LENGTH,
    since each WhatsApp message is a single URL-encoded GET request).
    """
    if limit < 1:
        raise ValueError("Batas harga harus minimal 1")
    if max_length < 1:
        raise ValueError("Panjang pesan harus minimal 1 karakter")

    ordered = sorted(
        records,
        key=lambda record: (
            comparison_price(record),
            str(record.get("commodity", "")),
            str(record.get("location", "")),
        ),
    )
    selected = ordered[:limit]
    header = [
        f"HARGA SEMBAKO TERMURAH — {date}",
        f"{len(ordered)} harga terpantau | menampilkan {len(selected)} teratas",
        "",
    ]
    lines: list[str] = []
    for index, record in enumerate(selected, start=1):
        brand = record.get("brand") or "Merek belum dicatat"
        product = record.get("productName") or record.get("commodity") or "Produk"
        unit = record.get("unit") or "unit"
        source_type = record.get("sourceType") or "sumber"
        area = AREAS.get(str(record.get("area")), {}).get("label", str(record.get("area", "")))
        location = record.get("location") or "Lokasi belum dicatat"
        lines.extend(
            [
                f"{index}. {product} — {brand}",
                f"   {price_description(record)} | {location} ({source_type})",
                f"   {area}",
            ]
        )
        if record.get("address"):
            lines.append(f"   {record['address']}")
        lines.append("")

    if not lines:
        lines = ["Belum ada harga yang dapat dikirim."]

    messages: list[str] = []
    current = "\n".join(header)
    for line in lines:
        remaining = line
        while remaining:
            available = max_length - len(current) - 1
            if available <= 0:
                if current.strip():
                    messages.append(current.rstrip())
                current = ""
                available = max_length

            if len(remaining) <= available:
                current = f"{current}\n{remaining}" if current else remaining
                remaining = ""
                continue

            # Prefer splitting at a space, but also split an unusually long
            # single word so the provider's request limit is never exceeded.
            split_at = remaining.rfind(" ", 0, available + 1)
            if split_at <= 0:
                split_at = available
            part = remaining[:split_at].rstrip()
            if not part:
                part = remaining[:available]
                split_at = available
            current = f"{current}\n{part}" if current else part
            messages.append(current.rstrip())
            current = ""
            remaining = remaining[split_at:].lstrip()
    if current.strip():
        messages.append(current.rstrip())
    return messages


def send_telegram_messages(
    messages: list[str],
    token: str | None = None,
    chat_id: str | None = None,
) -> int:
    """Send one or more messages using the official Telegram Bot API."""
    bot_token = token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    recipient = chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")
    if not bot_token or not recipient:
        raise RuntimeError(
            "Telegram belum dikonfigurasi. Isi TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID."
        )
    if not messages:
        raise RuntimeError("Tidak ada pesan Telegram yang dapat dikirim.")

    endpoint = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    for message in messages:
        request = Request(
            endpoint,
            data=json.dumps(
                {
                    "chat_id": recipient,
                    "text": message,
                    "disable_web_page_preview": True,
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "PelacakHargaSembako/1.0",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8", errors="replace"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
            raise RuntimeError(f"Gagal menghubungi Telegram: {error}") from error
        if not result.get("ok"):
            description = result.get("description", "Telegram menolak pesan")
            raise RuntimeError(f"Telegram menolak pesan: {description}")
    return len(messages)


def send_telegram_notification(
    records: list[dict[str, Any]],
    date: str,
    limit: int = 40,
) -> int:
    return send_telegram_messages(build_telegram_messages(records, date, limit))


# --- WhatsApp via CallMeBot (gratis, personal use only) -----------------
#
# CallMeBot BUKAN WhatsApp Cloud API resmi dari Meta — ini layanan gratis
# pihak ketiga yang meneruskan pesan ke satu nomor WhatsApp pribadi.
# Setup (sekali saja, manual lewat WhatsApp kamu sendiri):
#   1. Simpan nomor bot CallMeBot sebagai kontak (nomornya bisa berubah,
#      cek https://www.callmebot.com/blog/free-api-whatsapp-messages/).
#   2. Kirim pesan "I allow callmebot to send me messages" ke kontak itu.
#   3. Tunggu balasan berisi API key (kadang sampai beberapa menit).
# API key + nomor kamu sendiri itu yang dipakai di WHATSAPP_APIKEY dan
# WHATSAPP_PHONE. Karena ini layanan gratis tak resmi, ada rate limit
# ketat — pesan dipecah lebih pendek (lihat WHATSAPP_MAX_MESSAGE_LENGTH)
# dan diberi jeda antar pesan supaya tidak ditolak/diblokir.
CALLMEBOT_ENDPOINT = "https://api.callmebot.com/whatsapp.php"
WHATSAPP_MAX_MESSAGE_LENGTH = 1200
WHATSAPP_SEND_DELAY_SECONDS = 3
WHATSAPP_MAX_RETRIES = 3
WHATSAPP_RETRY_BACKOFF_SECONDS = 2


def normalize_whatsapp_phone(value: str) -> str:
    """Normalize a phone number to CallMeBot's international digit format."""
    phone = str(value or "").strip()
    if phone.startswith("+"):
        phone = phone[1:]
    phone = re.sub(r"[\s().-]", "", phone)
    if not re.fullmatch(r"\d{8,15}", phone):
        raise ValueError(
            f"Nomor WhatsApp tidak valid: {value!r}. "
            "Gunakan format internasional, misalnya 6281234567890."
        )
    return phone


def _split_secret_list(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"[\n,;]+", value or "") if item.strip()]


def parse_whatsapp_recipients(
    value: str | None = None,
    phone: str | None = None,
    apikey: str | None = None,
) -> list[tuple[str, str]]:
    """Read WhatsApp recipients while keeping the old single-recipient envs.

    Preferred format for several recipients is WHATSAPP_RECIPIENTS:
    ``628111111111=key-satu,628222222222=key-dua``.
    One recipient per line is also supported. JSON is accepted for secrets
    managers that make structured values easier to maintain:
    ``[{"phone": "...", "apikey": "..."}]``.
    """
    raw = value if value is not None else os.environ.get("WHATSAPP_RECIPIENTS", "")
    entries: list[tuple[str, str]] = []

    if raw.strip():
        parsed: Any = None
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = None

        if isinstance(parsed, dict):
            parsed = [
                {"phone": recipient_phone, "apikey": recipient_key}
                for recipient_phone, recipient_key in parsed.items()
            ]

        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict):
                    entries.append(
                        (str(item.get("phone", "")), str(item.get("apikey", "")))
                    )
                elif isinstance(item, str):
                    parts = re.split(r"\s*(?:=|\||:)\s*", item, maxsplit=1)
                    if len(parts) == 2:
                        entries.append((parts[0], parts[1]))
        else:
            for item in _split_secret_list(raw):
                parts = re.split(r"\s*(?:=|\||:)\s*", item, maxsplit=1)
                if len(parts) != 2:
                    raise ValueError(
                        "Format WHATSAPP_RECIPIENTS harus "
                        "nomor=apikey, satu penerima per baris."
                    )
                entries.append((parts[0], parts[1]))
    else:
        configured_phone = phone or os.environ.get("WHATSAPP_PHONE", "")
        configured_key = apikey or os.environ.get("WHATSAPP_APIKEY", "")
        phones = _split_secret_list(configured_phone)
        keys = _split_secret_list(configured_key)
        if len(phones) > 1 and len(keys) not in {1, len(phones)}:
            raise ValueError(
                "Jumlah WHATSAPP_APIKEY harus satu atau sama dengan jumlah "
                "WHATSAPP_PHONE."
            )
        if phones and keys:
            entries = [
                (recipient_phone, keys[0] if len(keys) == 1 else keys[index])
                for index, recipient_phone in enumerate(phones)
            ]

    if not entries:
        raise ValueError(
            "WhatsApp belum dikonfigurasi. Isi WHATSAPP_RECIPIENTS atau "
            "WHATSAPP_PHONE dan WHATSAPP_APIKEY."
        )

    recipients: list[tuple[str, str]] = []
    seen_phones: set[str] = set()
    for recipient_phone, recipient_key in entries:
        normalized_phone = normalize_whatsapp_phone(recipient_phone)
        normalized_key = str(recipient_key or "").strip()
        if not normalized_key:
            raise ValueError(f"API key WhatsApp kosong untuk nomor {normalized_phone}.")
        # A repeated phone must not receive duplicate notifications just
        # because it appeared twice in a secret.
        if normalized_phone in seen_phones:
            continue
        seen_phones.add(normalized_phone)
        recipients.append((normalized_phone, normalized_key))
    return recipients


def build_whatsapp_messages(
    records: list[dict[str, Any]],
    date: str,
    limit: int = 20,
) -> list[str]:
    return build_telegram_messages(records, date, limit, max_length=WHATSAPP_MAX_MESSAGE_LENGTH)


def _whatsapp_error_is_retryable(error: BaseException) -> bool:
    if isinstance(error, HTTPError):
        return error.code in {408, 425, 429, 500, 502, 503, 504}
    return isinstance(error, (URLError, TimeoutError))


def _send_one_whatsapp_message(phone: str, apikey: str, message: str) -> None:
    query = urlencode({"phone": phone, "text": message, "apikey": apikey})
    request = Request(
        f"{CALLMEBOT_ENDPOINT}?{query}",
        headers={"User-Agent": "PelacakHargaSembako/1.0"},
        method="GET",
    )
    last_error: BaseException | None = None
    for attempt in range(WHATSAPP_MAX_RETRIES):
        retryable = False
        try:
            with urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8", errors="replace")
            lowered_body = body.lower()
            if "message queued" in lowered_body or "message sent" in lowered_body:
                return
            raise RuntimeError(f"CallMeBot menolak pesan: {body.strip()[:200]}")
        except HTTPError as error:
            response_body = error.read().decode("utf-8", errors="replace")
            last_error = RuntimeError(
                f"HTTP {error.code}: {response_body.strip()[:200] or error.reason}"
            )
            retryable = _whatsapp_error_is_retryable(error)
        except (URLError, TimeoutError, RuntimeError) as error:
            last_error = error
            retryable = _whatsapp_error_is_retryable(error)

        if not retryable or attempt + 1 >= WHATSAPP_MAX_RETRIES:
            break
        time.sleep(WHATSAPP_RETRY_BACKOFF_SECONDS * (attempt + 1))

    raise RuntimeError(str(last_error or "CallMeBot gagal mengirim pesan"))


def send_whatsapp_messages(
    messages: list[str],
    phone: str | None = None,
    apikey: str | None = None,
) -> int:
    """Send messages to one or more CallMeBot recipients.

    A failed recipient is isolated so the remaining recipients still receive
    the notification. The final error reports partial delivery instead of
    pretending that all recipients succeeded.
    """
    if not messages:
        raise RuntimeError("Tidak ada pesan WhatsApp yang dapat dikirim.")

    try:
        recipients = parse_whatsapp_recipients(phone=phone, apikey=apikey)
    except ValueError as error:
        raise RuntimeError(str(error)) from error

    sent_count = 0
    errors: list[str] = []
    total_requests = len(recipients) * len(messages)
    request_number = 0
    for recipient_phone, recipient_key in recipients:
        for index, message in enumerate(messages, start=1):
            request_number += 1
            try:
                _send_one_whatsapp_message(recipient_phone, recipient_key, message)
                sent_count += 1
            except RuntimeError as error:
                errors.append(
                    f"{recipient_phone} (pesan {index}/{len(messages)}): {error}"
                )
                # Do not send later chunks to a recipient whose previous
                # request failed; continue with other recipients instead.
                break
            if request_number < total_requests:
                time.sleep(WHATSAPP_SEND_DELAY_SECONDS)

    if errors:
        detail = "; ".join(errors[:3])
        if len(errors) > 3:
            detail += f"; dan {len(errors) - 3} kegagalan lain"
        raise RuntimeError(
            f"{sent_count} dari {total_requests} target pesan WhatsApp terkirim. {detail}"
        )
    return sent_count


def send_whatsapp_notification(
    records: list[dict[str, Any]],
    date: str,
    limit: int = 20,
) -> int:
    return send_whatsapp_messages(build_whatsapp_messages(records, date, limit))


def print_report(
    date: str,
    records: list[dict[str, Any]],
    trends: list[dict[str, Any]],
    errors: list[str],
    transport: float,
) -> None:
    print(f"\nPelacak Harga Sembako — {date}")
    print("Sumber utama: SISKAPERBAPO, harga konsumen per pasar")
    location_count = len({(record["area"], record["marketId"]) for record in records})
    print(f"Lokasi terbaca: {location_count}")

    print("\nHarga termurah terpantau:")
    commodity_keys = dict.fromkeys(record["commodityKey"] for record in records)
    for commodity_key in commodity_keys:
        candidates = [
            record
            for record in records
            if record["commodityKey"] == commodity_key
        ]
        if not candidates:
            continue
        cheapest = min(candidates, key=lambda record: comparison_price(record) + transport)
        print(
            f"- {cheapest['commodity']}: {price_description(cheapest)} "
            f"— {cheapest['location']}, {AREAS[cheapest['area']]['label']}"
        )
        if transport:
            print(
                "  Estimasi satu unit + ongkos lokasi: "
                f"{currency(comparison_price(cheapest) + transport)}/{cheapest['unit']}"
            )

    print("\nSinyal tren:")
    warnings = [trend for trend in trends if trend["signal"] == "WASPADA NAIK"]
    cheap = [trend for trend in trends if trend["signal"] == "MURAH"]
    if not warnings and not cheap:
        print("- Belum ada peringatan; riwayat akan semakin berguna setelah dijalankan beberapa hari.")
    for trend in warnings:
        print(
            f"- WASPADA NAIK: {trend['commodity']} ({AREAS[trend['area']]['label']}) "
            f"— {currency(trend['latestPrice'])}/{trend['unit']}; {trend['reason']}"
        )
    for trend in cheap:
        print(
            f"- MURAH: {trend['commodity']} ({AREAS[trend['area']]['label']}) "
            f"— {currency(trend['latestPrice'])}/{trend['unit']}; {trend['reason']}"
        )

    if errors:
        print("\nSumber yang gagal dibaca:")
        for error in errors:
            print(f"- {error}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pelacak harga sembako Gresik-Lamongan")
    parser.add_argument(
        "--date",
        default=today_jakarta(),
        type=iso_date_argument,
        help="Tanggal data YYYY-MM-DD",
    )
    parser.add_argument("--areas", default="gresik,lamongan", help="Wilayah, dipisahkan koma")
    parser.add_argument("--commodities", default="all", help="Commodity key, dipisahkan koma")
    parser.add_argument(
        "--transport",
        type=non_negative_number,
        default=0,
        help="Ongkos perjalanan per lokasi",
    )
    parser.add_argument("--history", help="Path riwayat CSV relatif terhadap folder proyek")
    parser.add_argument("--retail", help="Path CSV toko/koperasi/swalayan relatif terhadap folder proyek")
    parser.add_argument("--report", help="Path laporan JSON relatif terhadap folder proyek")
    parser.add_argument(
        "--telegram",
        action="store_true",
        help="Kirim daftar harga termurah ke Telegram memakai environment secret",
    )
    parser.add_argument(
        "--telegram-limit",
        type=positive_integer,
        default=40,
        help="Jumlah harga teratas yang dikirim ke Telegram",
    )
    parser.add_argument(
        "--whatsapp",
        action="store_true",
        help="Kirim daftar harga termurah ke WhatsApp lewat CallMeBot (gratis, personal)",
    )
    parser.add_argument(
        "--whatsapp-limit",
        type=positive_integer,
        default=20,
        help="Jumlah harga teratas yang dikirim ke WhatsApp",
    )
    parser.add_argument(
        "--no-national",
        action="store_true",
        help="Lewati pengambilan referensi gabah nasional (Bapanas/PIHPS/BPS)",
    )
    parser.add_argument(
        "--hpp-kdmp",
        type=positive_integer,
        default=HPP_KDMP_DEFAULT,
        help="Acuan HPP Bulog/KDMP saat ini (ganti kalau ada Perbadan/SK baru)",
    )
    parser.add_argument(
        "--pengepul-price",
        default="",
        help="Harga pengepul hasil cek manual (tidak ada sumber publik otomatis)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        areas = selected_areas(args.areas)
        commodities = selected_commodities(args.commodities)
    except ValueError as error:
        print(f"Gagal: {error}", file=sys.stderr)
        return 2
    history_path = project_path(args.history, DEFAULT_HISTORY)
    retail_path = project_path(args.retail, DEFAULT_RETAIL)
    report_path = project_path(args.report, DEFAULT_REPORT)
    errors: list[str] = []
    current_records: list[dict[str, Any]] = []

    for area in areas:
        try:
            markets = fetch_markets(area)
            for market in markets:
                try:
                    current_records.extend(fetch_market_prices(args.date, area, market, commodities))
                except RuntimeError as error:
                    errors.append(f"{AREAS[area]['label']} / {market['psr_nama']}: {error}")
        except (RuntimeError, json.JSONDecodeError) as error:
            errors.append(f"{AREAS[area]['label']}: {error}")

    commodity_keys = {commodity.key for commodity in commodities}
    retail_records = [
        record
        for record in read_csv_records(retail_path)
        if record["date"] == args.date
        and record["area"] in areas
        and record["commodityKey"] in commodity_keys
    ]
    if not current_records and not retail_records:
        print("Gagal: tidak ada harga yang berhasil dibaca.", file=sys.stderr)
        return 1
    if not current_records and errors:
        print(
            "Peringatan: sumber pasar gagal; laporan hanya berisi data retail.",
            file=sys.stderr,
        )

    previous_history = read_csv_records(history_path)
    all_current_records = [*current_records, *retail_records]
    merged_history = merge_history(previous_history, all_current_records)
    write_csv_records(history_path, merged_history)
    report_records = [
        {
            **record,
            "unitPrice": round(comparison_price(record), 2),
        }
        for record in all_current_records
    ]

    trends = []
    for area in areas:
        for commodity in commodities:
            trends.append(
                trend_signal(
                    merged_history,
                    args.date,
                    area,
                    commodity,
                    [
                        record
                        for record in current_records
                        if record["area"] == area and record["commodityKey"] == commodity.key
                    ],
                )
            )

    report = {
        "generatedAt": jakarta_now_iso(),
        "date": args.date,
        "areas": areas,
        "source": SOURCE_BASE,
        "retailCoverage": {
            "records": len(retail_records),
            "message": (
                "Harga retail ikut dibandingkan."
                if retail_records
                else "Belum ada harga retail bermerek. Tambahkan data/retail-prices.csv."
            ),
        },
        "coverage": {
            "marketRecords": len(current_records),
            "retailRecords": len(retail_records),
            "partial": bool(errors),
        },
        "records": report_records,
        "trends": trends,
        "errors": errors,
    }
    if not args.no_national:
        national = fetch_national_reference_prices(
            args.date,
            hpp_kdmp=args.hpp_kdmp,
            pengepul_manual=args.pengepul_price,
        )
        report["nationalReferences"] = national
        try:
            append_national_reference_history(DEFAULT_NATIONAL_HISTORY, national)
        except OSError as error:
            print(f"Peringatan: gagal menyimpan riwayat referensi nasional: {error}", file=sys.stderr)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print_report(args.date, all_current_records, trends, errors, args.transport)
    print(f"\nRiwayat tersimpan: {history_path}")
    print(f"Laporan JSON: {report_path}")
    if not args.no_national:
        national = report["nationalReferences"]
        print("\nReferensi gabah nasional/daerah (di luar SISKAPERBAPO):")
        print(f"  Panel Bapanas          : {national['panelBapanas']}")
        print(f"  PIHPS                  : {national['pihps']}")
        print(f"  BPS Gresik (bulanan)   : {national['bpsGresik']}")
        print(f"  BPS Lamongan (bulanan) : {national['bpsLamongan']}")
        print(f"  Acuan HPP Bulog/KDMP   : {national['hppKdmp']}")
        print(f"  Pengepul (manual)      : {national['pengepulManual'] or '(belum diisi)'}")
    if not retail_records:
        print(f"Harga toko/koperasi/swalayan belum ada. Tambahkan data ke: {retail_path}")
    if args.telegram:
        try:
            sent_count = send_telegram_notification(
                all_current_records,
                args.date,
                args.telegram_limit,
            )
        except RuntimeError as error:
            print(f"\nGagal mengirim Telegram: {error}", file=sys.stderr)
            return 1
        print(f"Telegram: notifikasi terkirim dalam {sent_count} pesan.")
    if args.whatsapp:
        try:
            sent_count = send_whatsapp_notification(
                all_current_records,
                args.date,
                args.whatsapp_limit,
            )
        except RuntimeError as error:
            print(f"\nGagal mengirim WhatsApp: {error}", file=sys.stderr)
            return 1
        print(f"WhatsApp: notifikasi terkirim dalam {sent_count} pesan.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())