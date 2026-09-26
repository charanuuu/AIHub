class ToolCallInfo {
  final String toolName;
  final Map<String, dynamic> arguments;
  final Map<String, dynamic>? result;
  final bool success;
  final String? error;
  final double executionTimeMs;

  ToolCallInfo({
    required this.toolName,
    required this.arguments,
    this.result,
    this.success = true,
    this.error,
    this.executionTimeMs = 0.0,
  });

  factory ToolCallInfo.fromJson(Map<String, dynamic> json) {
    return ToolCallInfo(
      toolName: json['tool_name'] ?? 'unknown_tool',
      arguments: Map<String, dynamic>.from(json['arguments'] ?? {}),
      result: json['result'] != null
          ? Map<String, dynamic>.from(json['result'])
          : null,
      success: json['success'] ?? true,
      error: json['error'],
      executionTimeMs: (json['execution_time_ms'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class ChatMessage {
  final String id;
  final String role; // 'user' or 'assistant'
  final String content;
  final List<ToolCallInfo> toolCalls;
  final DateTime createdAt;
  final bool isError;

  ChatMessage({
    required this.id,
    required this.role,
    required this.content,
    this.toolCalls = const [],
    required this.createdAt,
    this.isError = false,
  });

  bool get isUser => role == 'user';
  bool get hasTools => toolCalls.isNotEmpty;

  factory ChatMessage.user(String content) {
    return ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      role: 'user',
      content: content,
      createdAt: DateTime.now(),
    );
  }

  factory ChatMessage.assistant({
    required String id,
    required String content,
    List<ToolCallInfo> toolCalls = const [],
    DateTime? createdAt,
  }) {
    return ChatMessage(
      id: id,
      role: 'assistant',
      content: content,
      toolCalls: toolCalls,
      createdAt: createdAt ?? DateTime.now(),
    );
  }

  factory ChatMessage.error(String errorMessage) {
    return ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      role: 'assistant',
      content: errorMessage,
      createdAt: DateTime.now(),
      isError: true,
    );
  }
}
