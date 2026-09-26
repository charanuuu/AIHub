import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/constants/app_colors.dart';
import '../../providers/chat_provider.dart';
import '../../providers/settings_provider.dart';
import '../history/history_drawer.dart';
import '../settings/settings_screen.dart';
import '../tools/tool_status_screen.dart';
import 'widgets/chat_input_bar.dart';
import 'widgets/message_bubble.dart';
import 'widgets/tool_shortcut_chips.dart';
import 'widgets/typing_indicator.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final settings = context.read<SettingsProvider>();
      settings.checkBackendHealth();
      context.read<ChatProvider>().fetchConversations(settings.backendUrl);
    });
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _handleSendMessage(String text) {
    final baseUrl = context.read<SettingsProvider>().backendUrl;
    context.read<ChatProvider>().sendMessage(text, baseUrl);
    _scrollToBottom();
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final chat = context.watch<ChatProvider>();
    final settings = context.watch<SettingsProvider>();
    final isDark = Theme.of(context).brightness == Brightness.dark;

    // Scroll to bottom when new messages arrive
    if (chat.messages.isNotEmpty || chat.isLoading) {
      _scrollToBottom();
    }

    return Scaffold(
      drawer: const HistoryDrawer(),
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('AI Hub', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            Row(
              children: [
                Container(
                  width: 7,
                  height: 7,
                  decoration: BoxDecoration(
                    color: settings.isBackendOnline ? AppColors.success : AppColors.error,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 5),
                Text(
                  settings.isBackendOnline
                      ? 'Connected · Live Tools Ready'
                      : 'Connecting to Backend...',
                  style: TextStyle(
                    fontSize: 11,
                    color: isDark ? Colors.white60 : Colors.black54,
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.build_rounded),
            tooltip: 'Tool Registry',
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const ToolStatusScreen()),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.add_comment_rounded),
            tooltip: 'New Chat',
            onPressed: () => chat.startNewConversation(),
          ),
          IconButton(
            icon: const Icon(Icons.settings_rounded),
            tooltip: 'Settings',
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const SettingsScreen()),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          const SizedBox(height: 6),
          // Tool Shortcuts
          ToolShortcutChips(
            onSelectShortcut: (query) => _handleSendMessage(query),
          ),
          const SizedBox(height: 6),

          // Messages View or Welcome Screen
          Expanded(
            child: chat.messages.isEmpty
                ? _buildEmptyState(context, isDark)
                : ListView.builder(
                    controller: _scrollController,
                    itemCount: chat.messages.length + (chat.isLoading ? 1 : 0),
                    itemBuilder: (context, index) {
                      if (index == chat.messages.length) {
                        return TypingIndicator(statusText: chat.statusText);
                      }
                      return MessageBubble(message: chat.messages[index]);
                    },
                  ),
          ),

          // Error banner with retry if network issue
          if (chat.errorMessage != null && !chat.isLoading)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              color: AppColors.error.withValues(alpha: 0.12),
              child: Row(
                children: [
                  const Icon(Icons.warning_amber_rounded, size: 18, color: AppColors.error),
                  const SizedBox(width: 8),
                  const Expanded(
                    child: Text(
                      'Connection or tool error occurred.',
                      style: TextStyle(fontSize: 12, color: AppColors.error),
                    ),
                  ),
                  TextButton(
                    onPressed: () => chat.retryLastMessage(settings.backendUrl),
                    child: const Text('Retry', style: TextStyle(color: AppColors.error)),
                  ),
                ],
              ),
            ),

          // Input Bar
          ChatInputBar(
            onSendMessage: _handleSendMessage,
            isLoading: chat.isLoading,
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context, bool isDark) {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.15),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.auto_awesome_rounded,
                size: 48,
                color: AppColors.primary,
              ),
            ),
            const SizedBox(height: 18),
            const Text(
              'Welcome to AI Hub',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              'Ask questions powered by real-time external tool execution.\nNo hallucinated data—pure verified live facts.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 13,
                color: isDark ? Colors.white60 : Colors.black54,
              ),
            ),
            const SizedBox(height: 24),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              alignment: WrapAlignment.center,
              children: [
                _buildExampleChip(
                  context,
                  'What is the weather in Bangalore tomorrow?',
                  Icons.wb_sunny_rounded,
                ),
                _buildExampleChip(
                  context,
                  'Convert 50,000 INR to USD.',
                  Icons.currency_exchange_rounded,
                ),
                _buildExampleChip(
                  context,
                  "Give me today's crypto market summary.",
                  Icons.currency_bitcoin_rounded,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildExampleChip(BuildContext context, String text, IconData icon) {
    return OutlinedButton.icon(
      style: OutlinedButton.styleFrom(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      ),
      icon: Icon(icon, size: 16),
      label: Text(text, style: const TextStyle(fontSize: 12)),
      onPressed: () => _handleSendMessage(text),
    );
  }
}
