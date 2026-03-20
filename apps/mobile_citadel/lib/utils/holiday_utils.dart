class HolidayUtils {
  static String getNextBigHoliday() {
    final now = DateTime.now();
    final year = now.year;
    
    final holidays = [
      Holiday("New Year's Day", DateTime(year, 1, 1)),
      Holiday("Valentine's Day", DateTime(year, 2, 14)),
      Holiday("St. Patrick's Day", DateTime(year, 3, 17)),
      Holiday("April Fool's Day", DateTime(year, 4, 1)),
      Holiday("Earth Day", DateTime(year, 4, 22)),
      Holiday("Halloween", DateTime(year, 10, 31)),
      Holiday("Thanksgiving", _calculateThanksgiving(year)),
      Holiday("Christmas", DateTime(year, 12, 25)),
      Holiday("New Year's Eve", DateTime(year, 12, 31)),
      
      // NEXT YEAR PRELOAD
      Holiday("New Year's Day (Next Year)", DateTime(year + 1, 1, 1)),
    ];
    
    // Sort logic
    holidays.sort((a, b) => a.date.compareTo(b.date));
    
    for (var h in holidays) {
      if (h.date.isAfter(now)) {
        final days = h.date.difference(now).inDays;
        return "The next major holiday is ${h.name} is in $days days, on ${_formatDate(h.date)}.";
      }
    }
    
    return "No upcoming holidays found in my database.";
  }
  
  static DateTime _calculateThanksgiving(int year) {
    // 4th Thursday of November
    DateTime temp = DateTime(year, 11, 1);
    int dayOfWeek = temp.weekday;
    int offset = (dayOfWeek <= DateTime.thursday) ? DateTime.thursday - dayOfWeek : 7 - (dayOfWeek - DateTime.thursday);
    return temp.add(Duration(days: offset + 21));
  }
  
  static String _formatDate(DateTime d) {
    final months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    return "${months[d.month - 1]} ${d.day}";
  }
}

class Holiday {
  final String name;
  final DateTime date;
  Holiday(this.name, this.date);
}
