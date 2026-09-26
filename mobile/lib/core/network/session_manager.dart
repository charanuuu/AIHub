import 'dart:io';
import 'dart:math';

/// Manages a persistent, cryptographically secure installation/session UUID
/// for AI'sHub client authentication and server-side conversation isolation.
class SessionManager {
  static const String _sessionFileName = '.aishub_session_id';
  static String? _cachedSessionId;

  // RFC 4122 UUID v4 regex pattern
  static final RegExp _uuidRegex = RegExp(
    r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$',
  );

  /// Retrieves the persistent session UUID.
  /// If not yet generated, creates a cryptographically strong UUID v4,
  /// saves it to local device storage, and returns it.
  static String getSessionId() {
    if (_cachedSessionId != null && _uuidRegex.hasMatch(_cachedSessionId!)) {
      return _cachedSessionId!;
    }

    try {
      final file = _resolveSessionFile();
      if (file.existsSync()) {
        final stored = file.readAsStringSync().trim();
        if (_uuidRegex.hasMatch(stored)) {
          _cachedSessionId = stored;
          return _cachedSessionId!;
        }
      }

      // Generate new cryptographically secure UUID v4
      final newUuid = generateSecureUuid();
      try {
        file.parent.createSync(recursive: true);
        file.writeAsStringSync(newUuid, flush: true);
      } catch (_) {
        // Fallback: If disk write is restricted, retain in memory for app runtime
      }
      _cachedSessionId = newUuid;
      return _cachedSessionId!;
    } catch (_) {
      _cachedSessionId ??= generateSecureUuid();
      return _cachedSessionId!;
    }
  }

  /// Generates a cryptographically strong UUID v4 (RFC 4122 compliant)
  /// using Dart's CSPRNG (Random.secure()).
  static String generateSecureUuid() {
    final Random random = Random.secure();
    final bytes = List<int>.generate(16, (_) => random.nextInt(256));

    // Set version to 4 (0100) -> 0x40
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    // Set variant to RFC 4122 (10xx) -> 0x80
    bytes[8] = (bytes[8] & 0x3f) | 0x80;

    final hex = bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).toList();
    return '${hex[0]}${hex[1]}${hex[2]}${hex[3]}-'
        '${hex[4]}${hex[5]}-'
        '${hex[6]}${hex[7]}-'
        '${hex[8]}${hex[9]}-'
        '${hex[10]}${hex[11]}${hex[12]}${hex[13]}${hex[14]}${hex[15]}';
  }

  /// Resolves the storage path for the persistent session file.
  static File _resolveSessionFile() {
    // 1. Android internal private files directory
    final androidFilesDir = Directory('/data/user/0/com.madan.aishub/files');
    if (androidFilesDir.existsSync()) {
      return File('${androidFilesDir.path}/$_sessionFileName');
    }

    // 2. Standard system temporary / sandbox directory
    final baseDir = Directory.systemTemp;
    return File('${baseDir.path}/$_sessionFileName');
  }

  /// Reset session for testing purposes only.
  static void resetForTesting([String? mockId]) {
    _cachedSessionId = mockId;
    try {
      final file = _resolveSessionFile();
      if (mockId != null) {
        file.writeAsStringSync(mockId, flush: true);
      } else if (file.existsSync()) {
        file.deleteSync();
      }
    } catch (_) {}
  }
}
