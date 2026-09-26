import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../core/constants/app_colors.dart';
import '../../../models/chat_message.dart';
import 'tool_execution_card.dart';

class MessageBubble extends StatelessWidget {
  final ChatMessage message;

  const MessageBubble({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final isUser = message.isUser;
    final timeStr = DateFormat('hh:mm a').format(message.createdAt);

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Column(
        crossAxisAlignment:
            isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment:
                isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (!isUser) ...[
                CircleAvatar(
                  radius: 16,
                  backgroundColor: AppColors.primary.withValues(alpha: 0.2),
                  child: const Icon(
                    Icons.auto_awesome_rounded,
                    size: 16,
                    color: AppColors.primaryLight,
                  ),
                ),
                const SizedBox(width: 8),
              ],
              Flexible(
                child: Container(
                  constraints: BoxConstraints(
                    maxWidth: MediaQuery.of(context).size.width * 0.78,
                  ),
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 12,
                  ),
                  decoration: BoxDecoration(
                    color: isUser
                        ? (isDark
                            ? AppColors.userBubbleDark
                            : AppColors.userBubbleLight)
                        : (message.isError
                            ? AppColors.error.withValues(alpha: 0.1)
                            : (isDark
                                ? AppColors.assistantBubbleDark
                                : AppColors.assistantBubbleLight)),
                    borderRadius: BorderRadius.only(
                      topLeft: const Radius.circular(18),
                      topRight: const Radius.circular(18),
                      bottomLeft: isUser
                          ? const Radius.circular(18)
                          : const Radius.circular(4),
                      bottomRight: isUser
                          ? const Radius.circular(4)
                          : const Radius.circular(18),
                    ),
                    border: !isUser
                        ? Border.all(
                            color: message.isError
                                ? AppColors.error.withValues(alpha: 0.4)
                                : (isDark
                                    ? AppColors.darkBorder
                                    : AppColors.lightBorder),
                            width: 1,
                          )
                        : null,
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // If assistant called tools, render tool execution cards
                      if (message.hasTools) ...[
                        for (final tool in message.toolCalls)
                          ToolExecutionCard(toolCall: tool),
                        const SizedBox(height: 8),
                      ],
                      // Main message text
                      Text(
                        message.content,
                        style: TextStyle(
                          fontSize: 14,
                          height: 1.45,
                          color: isUser
                              ? Colors.white
                              : (message.isError
                                  ? AppColors.error
                                  : (isDark ? Colors.white : Colors.black87)),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              if (isUser) ...[
                const SizedBox(width: 8),
                CircleAvatar(
                  radius: 16,
                  backgroundColor: AppColors.accent.withValues(alpha: 0.2),
                  child: const Icon(
                    Icons.person_rounded,
                    size: 16,
                    color: AppColors.accent,
                  ),
                ),
              ],
            ],
          ),
          Padding(
            padding: EdgeInsets.only(
              left: isUser ? 0 : 40,
              right: isUser ? 40 : 0,
              top: 4,
            ),
            child: Text(
              timeStr,
              style: TextStyle(
                fontSize: 10,
                color: isDark ? Colors.white38 : Colors.black38,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
