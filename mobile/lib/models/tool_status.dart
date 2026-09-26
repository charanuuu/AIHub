class ToolStatus {
  final String name;
  final String category;
  final String description;
  final String status; // 'active' or 'planned'
  final String provider;

  ToolStatus({
    required this.name,
    required this.category,
    required this.description,
    required this.status,
    required this.provider,
  });

  bool get isActive => status.toLowerCase() == 'active';

  factory ToolStatus.fromJson(Map<String, dynamic> json) {
    return ToolStatus(
      name: json['name'] ?? '',
      category: json['category'] ?? 'General',
      description: json['description'] ?? '',
      status: json['status'] ?? 'planned',
      provider: json['provider'] ?? 'external',
    );
  }
}
