import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class NeuralContact {
  final String id; // Matches native contact ID
  final String? profession;
  final String? locationLabel;
  final String? themePreference; // water, orbs, grid, nebula, matrix, network
  final String? customImagePath;
  final bool isFavorite;

  NeuralContact({
    required this.id,
    this.profession,
    this.locationLabel,
    this.themePreference,
    this.customImagePath,
    this.isFavorite = false,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'profession': profession,
      'location_label': locationLabel,
      'theme_preference': themePreference,
      'custom_image_path': customImagePath,
      'is_favorite': isFavorite ? 1 : 0,
    };
  }

  factory NeuralContact.fromMap(Map<String, dynamic> map) {
    return NeuralContact(
      id: map['id'],
      profession: map['profession'],
      locationLabel: map['location_label'],
      themePreference: map['theme_preference'],
      customImagePath: map['custom_image_path'],
      isFavorite: (map['is_favorite'] ?? 0) == 1,
    );
  }
}

class DatabaseService {
  static final DatabaseService _instance = DatabaseService._internal();
  static Database? _database;

  factory DatabaseService() => _instance;

  DatabaseService._internal();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDatabase();
    return _database!;
  }

  Future<Database> _initDatabase() async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, 'neural_cortex.db');

    return await openDatabase(
       path,
       version: 3,
       onCreate: (db, version) async {
         await db.execute('''
           CREATE TABLE neural_contacts(
             id TEXT PRIMARY KEY,
             profession TEXT,
             location_label TEXT,
             theme_preference TEXT,
             custom_image_path TEXT,
             is_favorite INTEGER DEFAULT 0
           )
         ''');
         
         await db.execute('''
           CREATE TABLE call_notes(
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             number TEXT,
             note TEXT,
             timestamp INTEGER
           )
         ''');
       },
       onUpgrade: (db, oldVersion, newVersion) async {
         if (oldVersion < 2) {
            await db.execute("ALTER TABLE neural_contacts ADD COLUMN is_favorite INTEGER DEFAULT 0");
         }
         if (oldVersion < 3) {
            await db.execute('''
               CREATE TABLE call_notes(
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 number TEXT,
                 note TEXT,
                 timestamp INTEGER
               )
            ''');
         }
       },
    );
  }

  // CRUD Operations

  Future<void> insertOrUpdateNeuralContact(NeuralContact contact) async {
    final db = await database;
    await db.insert(
      'neural_contacts',
      contact.toMap(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<NeuralContact?> getNeuralContact(String id) async {
    final db = await database;
    final List<Map<String, dynamic>> maps = await db.query(
      'neural_contacts',
      where: 'id = ?',
      whereArgs: [id],
    );

    if (maps.isNotEmpty) {
      return NeuralContact.fromMap(maps.first);
    }
    return null;
  }

  Future<List<NeuralContact>> getAllNeuralContacts() async {
    final db = await database;
    final List<Map<String, dynamic>> maps = await db.query('neural_contacts');
    return List.generate(maps.length, (i) => NeuralContact.fromMap(maps[i]));
  }

  Future<void> deleteNeuralContact(String id) async {
    final db = await database;
    await db.delete(
      'neural_contacts',
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<List<NeuralContact>> getFavoriteContacts() async {
    final db = await database;
    final List<Map<String, dynamic>> maps = await db.query(
      'neural_contacts',
      where: 'is_favorite = 1',
    );
    return List.generate(maps.length, (i) => NeuralContact.fromMap(maps[i]));
  }

  // NOTES OPERATIONS
  Future<void> addCallNote(String number, String note) async {
    final db = await database;
    final normalized = number.replaceAll(RegExp(r'\D'), '');

    // STORAGE LIMIT: Keep only last 5 notes (FIFO)
    final count = Sqflite.firstIntValue(await db.rawQuery(
      'SELECT COUNT(*) FROM call_notes WHERE number = ?', [normalized]
    ));

    if (count != null && count >= 5) {
       // Delete oldest note for this number
       await db.execute('''
          DELETE FROM call_notes 
          WHERE id = (SELECT id FROM call_notes WHERE number = ? ORDER BY timestamp ASC LIMIT 1)
       ''', [normalized]);
    }

    await db.insert('call_notes', {
      'number': normalized,
      'note': note,
      'timestamp': DateTime.now().millisecondsSinceEpoch
    });
  }
  
  Future<void> deleteCallNote(int id) async {
    final db = await database;
    await db.delete('call_notes', where: 'id = ?', whereArgs: [id]);
  }

  Future<List<Map<String, dynamic>>> getCallNotes(String number) async {
    final db = await database;
    final normalized = number.replaceAll(RegExp(r'\D'), '');
    return await db.query(
      'call_notes',
      where: 'number LIKE ?', 
      whereArgs: ['%$normalized'], // Loose match for suffixes
      orderBy: 'timestamp DESC'
    );
  }
}
