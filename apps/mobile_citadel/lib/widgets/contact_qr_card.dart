import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:google_fonts/google_fonts.dart';

class ContactQrCard extends StatelessWidget {
  final String name;
  final String number;
  final String email;

  const ContactQrCard({
    super.key,
    required this.name,
    required this.number,
    this.email = "",
  });

  @override
  Widget build(BuildContext context) {
    // vCard Format
    final vCard = 
      "BEGIN:VCARD\n"
      "VERSION:3.0\n"
      "FN:$name\n"
      "TEL:$number\n"
      "EMAIL:$email\n"
      "END:VCARD";

    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(color: Colors.cyanAccent.withOpacity(0.2), blurRadius: 20, spreadRadius: 5)
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          QrImageView(
            data: vCard,
            version: QrVersions.auto,
            size: 200.0,
            backgroundColor: Colors.white,
            eyeStyle: const QrEyeStyle(eyeShape: QrEyeShape.square, color: Colors.black),
            dataModuleStyle: const QrDataModuleStyle(dataModuleShape: QrDataModuleShape.square, color: Colors.black),
          ),
          const SizedBox(height: 16),
          Text(name.toUpperCase(), style: GoogleFonts.orbitron(color: Colors.black, fontWeight: FontWeight.bold, fontSize: 18)),
          Text(number, style: GoogleFonts.sourceCodePro(color: Colors.black54, fontSize: 14)),
        ],
      ),
    );
  }
}
