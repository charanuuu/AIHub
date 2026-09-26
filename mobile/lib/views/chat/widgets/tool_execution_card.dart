import 'dart:convert';
import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../../models/chat_message.dart';

class ToolExecutionCard extends StatefulWidget {
  final ToolCallInfo toolCall;

  const ToolExecutionCard({super.key, required this.toolCall});

  @override
  State<ToolExecutionCard> createState() => _ToolExecutionCardState();
}

class _ToolExecutionCardState extends State<ToolExecutionCard> {
  bool _isExpanded = false;

  Color _getToolColor(String name) {
    if (name.contains('weather')) return AppColors.toolWeather;
    if (name.contains('crypto')) return AppColors.toolCrypto;
    if (name.contains('currency')) return AppColors.toolCurrency;
    if (name.contains('finance') || name.contains('market')) return AppColors.toolFinance;
    if (name.contains('news')) return AppColors.toolNews;
    return AppColors.accent;
  }

  IconData _getToolIcon(String name) {
    if (name.contains('weather')) return Icons.wb_sunny_rounded;
    if (name.contains('crypto')) return Icons.currency_bitcoin_rounded;
    if (name.contains('currency')) return Icons.currency_exchange_rounded;
    if (name.contains('finance') || name.contains('market')) return Icons.trending_up_rounded;
    if (name.contains('news')) return Icons.newspaper_rounded;
    return Icons.build_circle_rounded;
  }

  @override
  Widget build(BuildContext context) {
    final tool = widget.toolCall;
    final color = _getToolColor(tool.toolName);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 6),
      decoration: BoxDecoration(
        color: isDark ? AppColors.darkCard.withValues(alpha: 0.5) : AppColors.lightCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: tool.success ? color.withValues(alpha: 0.4) : AppColors.error.withValues(alpha: 0.4),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          InkWell(
            borderRadius: BorderRadius.circular(12),
            onTap: () => setState(() => _isExpanded = !_isExpanded),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: color.withValues(alpha: 0.15),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(_getToolIcon(tool.toolName), size: 16, color: color),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(
                              tool.toolName,
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 13,
                                color: color,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: tool.success
                                    ? AppColors.success.withValues(alpha: 0.15)
                                    : AppColors.error.withValues(alpha: 0.15),
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: Text(
                                tool.success ? 'Success' : 'Failed',
                                style: TextStyle(
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                  color: tool.success ? AppColors.success : AppColors.error,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 2),
                        Text(
                          'Executed in ${tool.executionTimeMs.toStringAsFixed(0)}ms',
                          style: TextStyle(
                            fontSize: 11,
                            color: isDark ? Colors.white54 : Colors.black54,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Icon(
                    _isExpanded ? Icons.expand_less_rounded : Icons.expand_more_rounded,
                    color: isDark ? Colors.white60 : Colors.black54,
                    size: 20,
                  ),
                ],
              ),
            ),
          ),
          if (_isExpanded) ...[
            const Divider(height: 1),
            Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Input Arguments:',
                    style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 4),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: isDark ? Colors.black26 : Colors.white,
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      const JsonEncoder.withIndent('  ').convert(tool.arguments),
                      style: const TextStyle(
                        fontFamily: 'monospace',
                        fontSize: 11,
                      ),
                    ),
                  ),
                  if (tool.result != null) ...[
                    const SizedBox(height: 8),
                    const Text(
                      'Live Tool Output:',
                      style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 4),
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: isDark ? Colors.black26 : Colors.white,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        const JsonEncoder.withIndent('  ').convert(tool.result),
                        style: const TextStyle(
                          fontFamily: 'monospace',
                          fontSize: 11,
                        ),
                      ),
                    ),
                  ],
                  if (tool.error != null) ...[
                    const SizedBox(height: 8),
                    Text(
                      'Error: ${tool.error}',
                      style: const TextStyle(
                        color: AppColors.error,
                        fontSize: 11,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}
