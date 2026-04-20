// mongo-init.js
// Runs once when the MongoDB container is first created.
// Creates the evalify_db database, collections, and a seed teacher + student.

db = db.getSiblingDB("evalify_db");

// ── Collections ──────────────────────────────────────────────────────────────
// MongoDB creates collections lazily, but explicit creation lets us add
// validators and indexes up-front.

db.createCollection("users");
db.createCollection("papers");
db.createCollection("submissions");
db.createCollection("results");

// ── Indexes ───────────────────────────────────────────────────────────────────
db.users.createIndex({ email: 1 }, { unique: true, sparse: true });      // teacher lookup
db.users.createIndex({ roll_no: 1 }, { unique: true, sparse: true });    // student lookup
db.papers.createIndex({ teacher_id: 1 });                                 // list teacher's papers
db.submissions.createIndex({ student_id: 1, paper_id: 1 });              // student result lookup
db.results.createIndex({ submission_id: 1 }, { unique: true });

// ── Seed Teacher ─────────────────────────────────────────────────────────────
// Password "Teacher@123" — bcrypt hash generated offline.
// In production, run a proper seed script after hashing with the app's bcrypt.
db.users.insertOne({
  role: "teacher",
  email: "teacher@evalify.local",
  // NOTE: replace this with a real bcrypt hash before production use
  password_hash: "$2b$12$PLACEHOLDER_TEACHER_HASH",
  name: "Default Teacher",
  created_at: new Date()
});

// ── Seed Student ─────────────────────────────────────────────────────────────
db.users.insertOne({
  role: "student",
  roll_no: "CS2025001",
  password_hash: "$2b$12$PLACEHOLDER_STUDENT_HASH",
  name: "Seed Student",
  subject: "MLOps",
  created_at: new Date()
});

print("evalify_db initialised with seed data.");
