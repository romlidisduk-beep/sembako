// Firebase (Firestore) untuk komentar live — gratis tier, tanpa login.
// Config ini memang dirancang publik; keamanan dijaga aturan Firestore
// (lihat firestore.rules di root proyek).
import { initializeApp } from 'firebase/app';
import { getFirestore, collection, addDoc, serverTimestamp, query, orderBy, limit, onSnapshot } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: "AIzaSyDRLWRmh4P7q2xbA_B4wQE3IXfrSUOZYHA",
  authDomain: "sembako-comment.firebaseapp.com",
  projectId: "sembako-comment",
  storageBucket: "sembako-comment.firebasestorage.app",
  messagingSenderId: "428684467947",
  appId: "1:428684467947:web:afe7fce6d5b1a501d128ae",
  measurementId: "G-4Z1QGRWV5X",
};

const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);

export type Komentar = {
  id: string;
  nama: string;
  isi: string;
  createdAt?: { seconds: number } | null;
};

const KOMENTAR_COLLECTION = 'komentar';

export function subscribeKomentar(cb: (rows: Komentar[]) => void, onError?: (e: Error) => void) {
  const q = query(
    collection(db, KOMENTAR_COLLECTION),
    orderBy('createdAt', 'desc'),
    limit(100),
  );
  return onSnapshot(q, (snap) => {
    cb(snap.docs.map((d) => ({ id: d.id, ...(d.data() as Omit<Komentar, 'id'>) })));
  }, (err) => onError?.(err));
}

export async function kirimKomentar(nama: string, isi: string): Promise<void> {
  await addDoc(collection(db, KOMENTAR_COLLECTION), {
    nama: nama.slice(0, 40),
    isi: isi.slice(0, 500),
    createdAt: serverTimestamp(),
  });
}
