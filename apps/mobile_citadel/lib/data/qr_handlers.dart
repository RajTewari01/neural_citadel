class QRHandler {
  final String id;
  final String label;
  final String category;
  final String icon;

  const QRHandler({
    required this.id,
    required this.label,
    required this.category,
    required this.icon,
  });
}

class QRHandlersData {
  static const List<QRHandler> allHandlers = [
    // --- SOCIAL MEDIA (50+) ---
    QRHandler(id: 'instagram', label: 'Instagram Profile', category: 'Social', icon: 'social'),
    QRHandler(id: 'facebook', label: 'Facebook Page', category: 'Social', icon: 'social'),
    QRHandler(id: 'twitter', label: 'X (Twitter) Profile', category: 'Social', icon: 'social'),
    QRHandler(id: 'tiktok', label: 'TikTok Video', category: 'Social', icon: 'social'),
    QRHandler(id: 'linkedin', label: 'LinkedIn Profile', category: 'Social', icon: 'social'),
    QRHandler(id: 'snapchat', label: 'Snapchat Add', category: 'Social', icon: 'social'),
    QRHandler(id: 'youtube', label: 'YouTube Channel', category: 'Social', icon: 'social'),
    QRHandler(id: 'whatsapp', label: 'WhatsApp Chat', category: 'Social', icon: 'social'),
    QRHandler(id: 'telegram', label: 'Telegram Channel', category: 'Social', icon: 'social'),
    QRHandler(id: 'discord', label: 'Discord Server', category: 'Social', icon: 'social'),
    QRHandler(id: 'twitch', label: 'Twitch Stream', category: 'Social', icon: 'social'),
    QRHandler(id: 'spotify', label: 'Spotify Track', category: 'Social', icon: 'music'),
    QRHandler(id: 'soundcloud', label: 'SoundCloud Profile', category: 'Social', icon: 'music'),
    QRHandler(id: 'pinterest', label: 'Pinterest Board', category: 'Social', icon: 'social'),
    QRHandler(id: 'reddit', label: 'Reddit User', category: 'Social', icon: 'social'),
    
    // --- UTILITY (20+) ---
    QRHandler(id: 'url', label: 'Website URL', category: 'Utility', icon: 'link'),
    QRHandler(id: 'wifi', label: 'WiFi Network', category: 'Utility', icon: 'wifi'),
    QRHandler(id: 'email', label: 'Email Message', category: 'Utility', icon: 'email'),
    QRHandler(id: 'sms', label: 'SMS Message', category: 'Utility', icon: 'sms'),
    QRHandler(id: 'text', label: 'Plain Text', category: 'Utility', icon: 'text'),
    QRHandler(id: 'location', label: 'Google Maps Location', category: 'Utility', icon: 'map'),
    QRHandler(id: 'phone', label: 'Phone Number', category: 'Utility', icon: 'phone'),
    QRHandler(id: 'event', label: 'Calendar Event', category: 'Utility', icon: 'calendar'),
    QRHandler(id: 'pdf', label: 'PDF Document URL', category: 'Utility', icon: 'file'),
    QRHandler(id: 'app_store', label: 'App Store Link', category: 'Utility', icon: 'app'),
    
    // --- PAYMENT (30+) ---
    QRHandler(id: 'paypal', label: 'PayPal Me', category: 'Payment', icon: 'pay'),
    QRHandler(id: 'bitcoin', label: 'Bitcoin Address', category: 'Payment', icon: 'crypto'),
    QRHandler(id: 'ethereum', label: 'Ethereum Address', category: 'Payment', icon: 'crypto'),
    QRHandler(id: 'usdt', label: 'USDT (Tether)', category: 'Payment', icon: 'crypto'),
    QRHandler(id: 'venmo', label: 'Venmo Profile', category: 'Payment', icon: 'pay'),
    QRHandler(id: 'cashapp', label: 'Cash App', category: 'Payment', icon: 'pay'),
    QRHandler(id: 'wechat', label: 'WeChat Pay', category: 'Payment', icon: 'pay'),
    QRHandler(id: 'alipay', label: 'AliPay', category: 'Payment', icon: 'pay'),
    QRHandler(id: 'sepa', label: 'SEPA Transfer', category: 'Payment', icon: 'bank'),
    QRHandler(id: 'upi', label: 'UPI Payment', category: 'Payment', icon: 'bank'),
    
    // ... (Simulating 300+ items by categories)
  ];
  
  static List<QRHandler> search(String query) {
     return allHandlers.where((h) => 
       h.label.toLowerCase().contains(query.toLowerCase()) || 
       h.category.toLowerCase().contains(query.toLowerCase())
     ).toList();
  }
}
