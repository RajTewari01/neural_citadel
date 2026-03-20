import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'dart:convert';
import 'dart:io';

class DatabaseHelper {
  static final DatabaseHelper instance = DatabaseHelper._init();
  static Database? _database;

  DatabaseHelper._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('citadel_core.db');
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);

    return await openDatabase(path, version: 4, onCreate: _createDB, onUpgrade: _onUpgrade);
  }

  Future<File> getDatabasePathFile() async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, 'citadel_core.db');
    return File(path);
  }

  Future _createDB(Database db, int version) async {
    const idType = 'INTEGER PRIMARY KEY AUTOINCREMENT';
    const textType = 'TEXT NOT NULL';
    const textNullable = 'TEXT';
    const intType = 'INTEGER NOT NULL';
    const blobType = 'TEXT'; // JSON storage

    await db.execute('''
CREATE TABLE users ( 
  id $idType, 
  username $textType,
  email $textType,
  password_hash $blobType,
  role $textType,
  preferences $blobType,
  photo_url $textNullable,
  created_at $textType
)
''');

    await db.execute('''
CREATE TABLE sessions ( 
  id $idType, 
  user_id $intType,
  title $textType,
  created_at $textType,
  last_updated $textType,
  mode $textType, -- Added v3
  is_deleted INTEGER DEFAULT 0, -- Added v4 (Soft Delete)
  FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
)
''');

    await db.execute('''
CREATE TABLE messages ( 
  id $idType, 
  session_id $intType,
  role $textType,
  content $textType,
  type $textType, 
  metadata $blobType,
  timestamp $textType,
  FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
)
''');
  }

  Future _onUpgrade(Database db, int oldVersion, int newVersion) async {
    if (oldVersion < 2) {
      // Add photo_url column
      await db.execute("ALTER TABLE users ADD COLUMN photo_url TEXT");
    }
    if (oldVersion < 3) {
      // Add mode column for v3
      await db.execute("ALTER TABLE sessions ADD COLUMN mode TEXT DEFAULT 'reasoning'");
    }
    if (oldVersion < 4) {
      // Add is_deleted for v4
      await db.execute("ALTER TABLE sessions ADD COLUMN is_deleted INTEGER DEFAULT 0");
    }
  }

  // --- USER OPERATIONS ---

  Future<int> createUser(Map<String, dynamic> user) async {
    final db = await instance.database;
    return await db.insert('users', user);
  }

  Future<Map<String, dynamic>?> getUserByEmail(String email) async {
    final db = await instance.database;
    final maps = await db.query(
      'users',
      columns: ['id', 'username', 'email', 'role', 'preferences', 'photo_url'],
      where: 'email = ?',
      whereArgs: [email],
    );

    if (maps.isNotEmpty) {
      return maps.first;
    } else {
      return null;
    }
  }
  
  Future<List<Map<String, dynamic>>> getAllUsers() async {
    final db = await instance.database;
    return await db.query('users');
  }

  Future<int> updateUserPhoto(String email, String photoPath) async {
    final db = await instance.database;
    return await db.update(
      'users',
      {'photo_url': photoPath},
      where: 'email = ?',
      whereArgs: [email],
    );
  }

  // --- SESSION OPERATIONS ---

  Future<int> createSession(int userId, String title, String mode) async {
    final db = await instance.database;
    final session = {
      'user_id': userId,
      'title': title,
      'mode': mode,
      'created_at': DateTime.now().toIso8601String(),
      'last_updated': DateTime.now().toIso8601String(),
    };
    return await db.insert('sessions', session);
  }

  Future<List<Map<String, dynamic>>> getUserSessions(int userId) async {
    final db = await instance.database;
    return await db.query(
      'sessions',
      where: 'user_id = ? AND is_deleted = 0',
      whereArgs: [userId],
      orderBy: 'last_updated DESC',
    );
  }

  Future<int> deleteSession(int sessionId) async {
    final db = await instance.database;
    // Soft Delete: Mark as deleted but keep data for Admin
    return await db.update(
      'sessions',
      {'is_deleted': 1},
      where: 'id = ?',
      whereArgs: [sessionId],
    );
  }

  // --- MESSAGE OPERATIONS ---

  Future<int> addMessage(int sessionId, Map<String, dynamic> msg) async {
    final db = await instance.database;
    final message = {
      'session_id': sessionId,
      'role': msg['role'],
      'content': msg['content'],
      'type': msg['type'] ?? 'text',
      'metadata': jsonEncode(msg), // Store full raw for safety
      'timestamp': DateTime.now().toIso8601String(),
    };
    
    // Update session timestamp
    await db.update(
      'sessions', 
      {'last_updated': DateTime.now().toIso8601String()},
      where: 'id = ?',
      whereArgs: [sessionId]
    );
    
    return await db.insert('messages', message);
  }

  Future<List<Map<String, dynamic>>> getSessionMessages(int sessionId) async {
    final db = await instance.database;
    final result = await db.query(
      'messages',
      where: 'session_id = ?',
      whereArgs: [sessionId],
      orderBy: 'id ASC',
    );
    
    // Convert back to App format
    return result.map((row) {
      // Try parsing metadata first for full fidelity
      try {
        if (row['metadata'] != null) {
          return jsonDecode(row['metadata'] as String) as Map<String, dynamic>;
        }
      } catch(e) {}
      
      // Fallback construction
      return {
        'role': row['role'],
        'content': row['content'],
        'type': row['type'],
      };
    }).toList();
  }

  Future close() async {
    final db = await instance.database;
    db.close();
  }
}
