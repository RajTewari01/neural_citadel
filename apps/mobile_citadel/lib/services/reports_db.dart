import 'dart:io';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'package:path_provider/path_provider.dart';

class ReportsDB {
  static final ReportsDB _instance = ReportsDB._internal();
  factory ReportsDB() => _instance;
  ReportsDB._internal();

  Database? _db;

  Future<Database> get db async {
    if (_db != null) return _db!;
    _db = await _initDB();
    return _db!;
  }

  Future<Database> _initDB() async {
    final docsDir = await getApplicationDocumentsDirectory();
    final path = join(docsDir.path, 'pending_reports.db');

    return await openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE reports(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT,
            steps TEXT,
            userId TEXT,
            screenshotPath TEXT,
            timestamp TEXT
          )
        ''');
      },
    );
  }

  Future<int> insertReport({
    required String description,
    required String steps,
    required String userId,
    required String screenshotPath,
  }) async {
    final dbClient = await db;
    // We need to persist the image too. 
    // Usually the image is in cache/temp which might get cleared.
    // It is safer to move it to app docs directory.
    
    final savedImage = await _saveImagePermanently(screenshotPath);
    
    return await dbClient.insert('reports', {
      'description': description,
      'steps': steps,
      'userId': userId,
      'screenshotPath': savedImage.path,
      'timestamp': DateTime.now().toIso8601String(),
    });
  }

  Future<File> _saveImagePermanently(String path) async {
    final file = File(path);
    if (!await file.exists()) return file; // Should not happen

    final docsDir = await getApplicationDocumentsDirectory();
    final newPath = join(docsDir.path, 'report_${DateTime.now().millisecondsSinceEpoch}.png');
    return await file.copy(newPath);
  }

  Future<List<Map<String, dynamic>>> getPendingReports() async {
    final dbClient = await db;
    return await dbClient.query('reports');
  }

  Future<void> deleteReport(int id) async {
    final dbClient = await db;
    // Get file path to delete it too
    final report = await dbClient.query('reports', where: 'id = ?', whereArgs: [id]);
    if (report.isNotEmpty) {
      final path = report.first['screenshotPath'] as String;
      final file = File(path);
      if (await file.exists()) {
        try { await file.delete(); } catch (_) {}
      }
    }
    
    await dbClient.delete('reports', where: 'id = ?', whereArgs: [id]);
  }
}
