import 'package:flutter/services.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_contacts/flutter_contacts.dart';
import 'package:permission_handler/permission_handler.dart';
import 'database_service.dart';

/// Combines native Android contact data with our local "Neural" metadata
class RichContact {
  final Contact nativeContact;
  final NeuralContact? neuralContact;

  RichContact({required this.nativeContact, this.neuralContact});

  String get displayName => nativeContact.displayName;
  String get id => nativeContact.id;
  List<Phone> get phones => nativeContact.phones;
  bool get isStarred => nativeContact.isStarred;
  set isStarred(bool value) => nativeContact.isStarred = value;
  
  // Neural Extensions
  String? get profession => neuralContact?.profession;
  String? get location => neuralContact?.locationLabel;
  String? get theme => neuralContact?.themePreference ?? 'default';
  String? get customImage => neuralContact?.customImagePath;
}

class ContactService extends ChangeNotifier {
  final DatabaseService _db = DatabaseService();
  List<RichContact> _cachedContacts = [];

  Future<void> init() async {
    final status = await Permission.contacts.request();
    if (status.isGranted) {
      await refreshContacts();
    }
  }

  Future<List<RichContact>> getContacts() async {
    if (_cachedContacts.isEmpty) {
      await refreshContacts();
    }
    return _cachedContacts;
  }

  Future<void> refreshContacts() async {
    if (await Permission.contacts.isGranted) {
      // 1. Fetch Native Contacts
      final nativeContacts = await FlutterContacts.getContacts(
        withProperties: true,
        withThumbnail: true, 
        withPhoto: true, 
        withAccounts: true, 
        sorted: true,
      );

      // 2. Fetch Neural Data
      final neuralContacts = await _db.getAllNeuralContacts();
      final neuralMap = {for (var c in neuralContacts) c.id: c};

      // 3. Merge
      _cachedContacts = nativeContacts.map((native) {
        return RichContact(
          nativeContact: native,
          neuralContact: neuralMap[native.id],
        );
      }).toList();
      notifyListeners(); 
    }
  }

  Future<List<RichContact>> searchContacts(String query) async {
    if (query.isEmpty) return _cachedContacts;
    
    final lowerQuery = query.toLowerCase();
    
    // T9 Helper: Convert name to digits (Standard ITU E.161)
    String nameToT9(String name) {
      return name.toUpperCase().split('').map((char) {
        if (RegExp(r'[A-C]').hasMatch(char)) return '2';
        if (RegExp(r'[D-F]').hasMatch(char)) return '3';
        if (RegExp(r'[G-I]').hasMatch(char)) return '4';
        if (RegExp(r'[J-L]').hasMatch(char)) return '5';
        if (RegExp(r'[M-O]').hasMatch(char)) return '6';
        if (RegExp(r'[P-S]').hasMatch(char)) return '7';
        if (RegExp(r'[T-V]').hasMatch(char)) return '8';
        if (RegExp(r'[W-Z]').hasMatch(char)) return '9';
        return ''; // Non-alpha chars ignored
      }).join();
    }

    return _cachedContacts.where((c) {
      final name = c.displayName;
      final nameMatch = name.toLowerCase().contains(lowerQuery);
      
      final cleanNum = c.phones.isNotEmpty ? c.phones.first.number.replaceAll(RegExp(r'\D'), '') : '';
      final phoneMatch = cleanNum.contains(query);
      
      // T9 Logic
      bool t9Match = false;
      if (RegExp(r'^[0-9]+$').hasMatch(query)) {
         final t9Name = nameToT9(name);
         // Match if T9 string contains query, OR if query matches name start (initials)
         t9Match = t9Name.contains(query);
      }

      return nameMatch || phoneMatch || t9Match;
    }).toList();
  }

  Future<RichContact?> getContactByNumber(String number) async {
    if (_cachedContacts.isEmpty) await refreshContacts();

    try {
      // 1. Sanitize Input: Remove everything except digits
      String cleanInput = number.replaceAll(RegExp(r'\D'), '');
      if (cleanInput.isEmpty) return null;

      // 2. Aggressive Suffix Match (The "Old Dialer" Method)
      // Most dialers match the last 7-10 digits to handle country codes (+91, 0, etc)
      // We will match the last 7 digits to be extremely safe against formatting issues.
      int matchLen = (cleanInput.length > 7) ? 7 : cleanInput.length;
      String needle = cleanInput.substring(cleanInput.length - matchLen);

      try {
        return _cachedContacts.cast<RichContact?>().firstWhere((c) {
            if (c == null) return false;
            return c.phones.any((p) {
                String pNum = p.number.replaceAll(RegExp(r'\D'), '');
                if (pNum.length < matchLen) return false;
                return pNum.endsWith(needle);
            });
        });
      } catch (_) {
        return null; // No match found
      }
    } catch (e) {
      print("Matching Error: $e");
      return null;
    }
  }

  Future<String?> addContact(String firstName, String lastName, String phone) async {
    if (await Permission.contacts.request().isGranted) {
      final newContact = Contact()
        ..name.first = firstName
        ..name.last = lastName
        ..phones = [Phone(phone)];
      
      final result = await newContact.insert();
      if (result != null) {
        await refreshContacts();
        return result.id;
      }
    }
    return null;
  }

  Future<bool> deleteContact(RichContact contact) async {
    try {
      await contact.nativeContact.delete();
      await _db.deleteNeuralContact(contact.id); // Clean up neural data too
      await refreshContacts();
      return true;
    } catch (e) {
      return false;
    }
  }

  Future<bool> setFavorite(RichContact contact, bool isStarred) async {
    try {
      contact.nativeContact.isStarred = isStarred;
      await contact.nativeContact.update();
      await refreshContacts();
      return true;
    } catch (e) {
      print("Fav Error: $e");
      return false;
    }
  }
  
  // Blocking Implementation (Native)
  final MethodChannel _platform = const MethodChannel('com.neuralcitadel/native');

  Future<bool> blockNumber(String number) async {
    try {
       await _platform.invokeMethod('blockNumber', {'number': number});
       return true;
    } catch (e) {
       print("Block failed: $e");
       return false;
    }
  }

  Future<bool> unblockNumber(String number) async {
    try {
       await _platform.invokeMethod('unblockNumber', {'number': number});
       return true;
    } catch (e) {
       print("Unblock failed: $e");
       return false;
    }
  }

  Future<List<String>> getBlockedNumbers() async {
    try {
       final List<dynamic> result = await _platform.invokeMethod('getBlockedNumbers');
       return result.cast<String>();
    } catch (e) {
       return [];
    }
  }

  // New: Update Neural Profile
  Future<void> updateNeuralProfile(String contactId, {String? profession, String? location, String? theme, String? imagePath}) async {
    final existing = await _db.getNeuralContact(contactId);
    final updated = NeuralContact(
      id: contactId,
      profession: profession ?? existing?.profession,
      locationLabel: location ?? existing?.locationLabel,
      themePreference: theme ?? existing?.themePreference,
      customImagePath: imagePath ?? existing?.customImagePath,
    );
    await _db.insertOrUpdateNeuralContact(updated);
    await refreshContacts(); // Refresh to propagate changes
  }
  Future<Contact?> getNativeContact(String id) async {
     return await FlutterContacts.getContact(id, withPhoto: true, withThumbnail: true, withProperties: true, withAccounts: true);
  }
}
