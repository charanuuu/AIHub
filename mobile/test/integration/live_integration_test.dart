import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:aihub/providers/settings_provider.dart';
import 'package:aihub/providers/tools_provider.dart';
import 'package:aihub/providers/chat_provider.dart';

void main() {
  setUpAll(() {
    HttpOverrides.global = null;
  });

  const backendUrl = 'http://127.0.0.1:8000';
  const offlineBackendUrl = 'http://127.0.0.1:9999';

  group('Live Flutter App End-to-End Integration Tests', () {
    test('1. SettingsProvider connects to live backend and verifies health', () async {
      final settings = SettingsProvider();
      settings.setBackendUrl(backendUrl);

      // Wait for async health check
      await settings.checkBackendHealth();

      expect(settings.isBackendOnline, isTrue, reason: 'Backend should be online');
      expect(settings.backendVersion, '1.0.0');
      expect(settings.activeToolsCount, 5);
      print('SettingsProvider: Health check PASSED (online=true, version=1.0.0, tools=5)');
    });

    test('2. ToolsProvider fetches all 5 active tools from live backend', () async {
      final toolsProvider = ToolsProvider();
      await toolsProvider.fetchTools(backendUrl);

      expect(toolsProvider.errorMessage, isNull);
      expect(toolsProvider.tools.length, 5);
      expect(toolsProvider.activeTools.length, 5);

      final toolNames = toolsProvider.tools.map((t) => t.name).toList();
      expect(toolNames, containsAll([
        'get_weather',
        'convert_currency',
        'get_crypto_summary',
        'get_market_quote',
        'get_latest_news',
      ]));
      print('ToolsProvider: Fetched 5 tools successfully: $toolNames');
    });

    test('3. ChatProvider sends real query, receives tool execution & response', () async {
      final chatProvider = ChatProvider();
      const query = 'What is the price of Bitcoin?';

      await chatProvider.sendMessage(query, backendUrl);

      expect(chatProvider.errorMessage, isNull);
      expect(chatProvider.messages.length, greaterThanOrEqualTo(2));

      final userMsg = chatProvider.messages.first;
      expect(userMsg.isUser, isTrue);
      expect(userMsg.content, query);

      final assistantMsg = chatProvider.messages.last;
      expect(assistantMsg.role, 'assistant');
      expect(assistantMsg.content, contains('Bitcoin'));
      expect(assistantMsg.toolCalls.isNotEmpty, isTrue);

      final toolCall = assistantMsg.toolCalls.first;
      expect(toolCall.toolName, 'get_crypto_summary');
      expect(chatProvider.currentConversationId, isNotNull);

      print('ChatProvider: Live response received with tool ${toolCall.toolName}');
      print('Conversation ID: ${chatProvider.currentConversationId}');
    });

    test('4. ChatProvider loads conversation history and persists across calls', () async {
      final chatProvider = ChatProvider();
      await chatProvider.fetchConversations(backendUrl);

      expect(chatProvider.conversations.isNotEmpty, isTrue);
      final firstConv = chatProvider.conversations.first;
      print('Found conversation: ${firstConv.id}, title: ${firstConv.title}');

      await chatProvider.loadConversation(firstConv.id, backendUrl);
      expect(chatProvider.currentConversationId, firstConv.id);
      expect(chatProvider.messages.isNotEmpty, isTrue);
      print('Loaded ${chatProvider.messages.length} messages from conversation history');
    });

    test('5. Error handling when backend is unavailable', () async {
      // 5a. SettingsProvider reports offline
      final settings = SettingsProvider();
      settings.setBackendUrl(offlineBackendUrl);
      await settings.checkBackendHealth();
      expect(settings.isBackendOnline, isFalse);

      // 5b. ChatProvider reports error gracefully
      final chatProvider = ChatProvider();
      await chatProvider.sendMessage('Hello', offlineBackendUrl);
      expect(chatProvider.errorMessage, isNotNull);
      expect(chatProvider.messages.isNotEmpty, isTrue);
      expect(chatProvider.messages.last.isError, isTrue);
      print('Error handling PASSED: Correctly caught backend unavailability');
    });
  });
}
