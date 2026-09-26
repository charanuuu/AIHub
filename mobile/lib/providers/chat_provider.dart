import 'package:flutter/foundation.dart';
import '../core/constants/api_endpoints.dart';
import '../core/network/api_client.dart';
import '../models/chat_message.dart';
import '../models/conversation.dart';

class ChatProvider with ChangeNotifier {
  final ApiClient _apiClient = ApiClient();

  final List<ChatMessage> _messages = [];
  List<ConversationSummary> _conversations = [];
  String? _currentConversationId;
  bool _isLoading = false;
  String _statusText = 'AI is thinking...';
  String? _errorMessage;
  String? _lastSentMessage;

  List<ChatMessage> get messages => _messages;
  List<ConversationSummary> get conversations => _conversations;
  String? get currentConversationId => _currentConversationId;
  bool get isLoading => _isLoading;
  String get statusText => _statusText;
  String? get errorMessage => _errorMessage;

  void startNewConversation() {
    _messages.clear();
    _currentConversationId = null;
    _errorMessage = null;
    notifyListeners();
  }

  Future<void> sendMessage(String text, String baseUrl) async {
    final query = text.trim();
    if (query.isEmpty) return;

    _lastSentMessage = query;
    _errorMessage = null;

    // Add user message to UI immediately
    final userMessage = ChatMessage.user(query);
    _messages.add(userMessage);
    _isLoading = true;
    _statusText = 'Routing to agent...';
    notifyListeners();

    try {
      final payload = {
        'message': query,
        if (_currentConversationId != null) 'conversation_id': _currentConversationId,
      };

      final response = await _apiClient.post(
        ApiEndpoints.chat(baseUrl),
        payload,
      );

      if (response != null && response is Map) {
        _currentConversationId = response['conversation_id'];

        final toolCallsRaw = response['tool_calls'];
        final List<ToolCallInfo> toolCalls = [];
        if (toolCallsRaw is List) {
          for (final tc in toolCallsRaw) {
            if (tc is Map) {
              toolCalls.add(ToolCallInfo.fromJson(Map<String, dynamic>.from(tc)));
            }
          }
        }

        final assistantMessage = ChatMessage.assistant(
          id: DateTime.now().millisecondsSinceEpoch.toString(),
          content: response['message'] ?? 'No response received.',
          toolCalls: toolCalls,
        );

        _messages.add(assistantMessage);
      }
    } catch (e) {
      _errorMessage = e.toString();
      _messages.add(ChatMessage.error(
        'Failed to get a response from AI Hub. $e',
      ));
    } finally {
      _isLoading = false;
      notifyListeners();
      fetchConversations(baseUrl);
    }
  }

  Future<void> retryLastMessage(String baseUrl) async {
    if (_lastSentMessage != null) {
      // Remove last error message if present
      if (_messages.isNotEmpty && _messages.last.isError) {
        _messages.removeLast();
      }
      // Remove last user message since sendMessage re-adds it
      if (_messages.isNotEmpty && _messages.last.isUser) {
        _messages.removeLast();
      }
      await sendMessage(_lastSentMessage!, baseUrl);
    }
  }

  Future<void> fetchConversations(String baseUrl) async {
    try {
      final response = await _apiClient.get(ApiEndpoints.conversations(baseUrl));
      if (response is List) {
        _conversations = response
            .map((c) => ConversationSummary.fromJson(Map<String, dynamic>.from(c)))
            .toList();
        notifyListeners();
      }
    } catch (_) {
      // Ignore background conversation sync errors
    }
  }

  Future<void> loadConversation(String conversationId, String baseUrl) async {
    _isLoading = true;
    _statusText = 'Loading history...';
    _errorMessage = null;
    notifyListeners();

    try {
      final response = await _apiClient.get(
        ApiEndpoints.conversationMessages(baseUrl, conversationId),
      );

      if (response is List) {
        _messages.clear();
        _currentConversationId = conversationId;

        for (final item in response) {
          final map = Map<String, dynamic>.from(item);
          final role = map['role'] ?? 'user';
          final content = map['content'] ?? '';
          final rawTools = map['tool_calls'];
          final List<ToolCallInfo> toolCalls = [];

          if (rawTools is List) {
            for (final t in rawTools) {
              if (t is Map) {
                toolCalls.add(ToolCallInfo.fromJson(Map<String, dynamic>.from(t)));
              }
            }
          }

          _messages.add(ChatMessage(
            id: map['id'] ?? DateTime.now().millisecondsSinceEpoch.toString(),
            role: role,
            content: content,
            toolCalls: toolCalls,
            createdAt: map['created_at'] != null
                ? DateTime.tryParse(map['created_at']) ?? DateTime.now()
                : DateTime.now(),
          ));
        }
      }
    } catch (e) {
      _errorMessage = 'Could not load conversation: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> deleteConversation(String conversationId, String baseUrl) async {
    try {
      await _apiClient.delete(ApiEndpoints.deleteConversation(baseUrl, conversationId));
      _conversations.removeWhere((c) => c.id == conversationId);
      if (_currentConversationId == conversationId) {
        startNewConversation();
      } else {
        notifyListeners();
      }
    } catch (e) {
      _errorMessage = 'Failed to delete conversation: $e';
      notifyListeners();
    }
  }

  @override
  void dispose() {
    _apiClient.dispose();
    super.dispose();
  }
}
