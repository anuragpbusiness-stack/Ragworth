// RAGWORTH SECURE FIREBASE CONFIGURATION
// Paste your standard Firebase web app credentials below.
// You can find this in your Firebase Console -> Project Settings -> General -> Your Apps.

const firebaseConfig = {
  apiKey: "YOUR_FIREBASE_API_KEY",
  authDomain: "ragworth-2026.firebaseapp.com",
  projectId: "ragworth-2026",
  storageBucket: "ragworth-2026.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
};

// TOGGLE SECURE FIREBASE NODE
// Set to true once you have pasted your valid credentials above!
// This will immediately migrate the dashboard to run 100% serverless, 
// communicating in real-time with Firebase Firestore 24/7 on the cloud!
const USE_FIREBASE = false;
