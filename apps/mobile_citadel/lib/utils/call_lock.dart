// Shared Lock for Call Screen existence
// This prevents "Double Screens" (e.g. Dialer pushes one, then Native pushes another)

class CallLock {
  static bool isActive = false;
  static String? lastNumber;
  static DateTime? lastTime;
}
