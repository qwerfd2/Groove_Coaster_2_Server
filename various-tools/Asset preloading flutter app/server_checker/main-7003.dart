import 'package:flutter/material.dart';
import 'dart:convert';
import 'dart:io';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:http/http.dart' as http;
import 'package:archive/archive.dart';

void main() {
  runApp(const MyApp());
}

Future<String> getSaveDir() async {
  final info = await PackageInfo.fromPlatform();
  if (Platform.isIOS) {
    return "/var/mobile/Containers/Data/Application/${info.buildNumber}/Library/Caches/";
  } else {
    return "/data/data/${info.packageName}/files/resource/";
  }
}

/// Root of the app
class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'GC2OS Asset Downloader',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: const HomeScreen(),
    );
  }
}

/// Home screen with inputs
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _serverController = TextEditingController();
  final TextEditingController _tokenController = TextEditingController();

  String _result = "";

  Future<void> initBatch(String serverUrl, String token) async {
    setState(() => _result = "Checking...");

    if (serverUrl.endsWith("/")) {
      serverUrl = serverUrl.substring(0, serverUrl.length - 1);
    }

    try {
      final url = Uri.parse('$serverUrl/batch');
      final payload = {
        "token": token,
        "platform": Platform.isIOS ? "iOS" : "Android",
      };
      final response = await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(payload),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data["error"] != null) {
          setState(() => _result = "Error: ${data["error"]}");
        } else {
          // Download stage files first
          await Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => DownloadScreen(
                files: Map<String, int>.from(data["stage"] ?? {}),
                threadCount: data["thread"] ?? 1,
                title: "Downloading Stages",
                serverUrl: serverUrl,
                token: token,
              ),
            ),
          );
          // Then download audio files
          await Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => DownloadScreen(
                files: Map<String, int>.from(data["audio"] ?? {}),
                threadCount: data["thread"] ?? 1,
                title: "Downloading Music",
                serverUrl: serverUrl,
                token: token,
              ),
            ),
          );
          setState(
            () => _result =
                "All downloads complete! You can now install the game back.",
          );
        }
      } else {
        setState(
          () => _result =
              "Server error: ${response.statusCode}, ${response.body}",
        );
      }
    } catch (e) {
      setState(() => _result = "Request failed: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("GC2OS Asset Downloader")),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _serverController,
              decoration: const InputDecoration(
                labelText: "Server URL",
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _tokenController,
              decoration: const InputDecoration(
                labelText: "Authorization Token",
                border: OutlineInputBorder(),
              ),
              obscureText: true, // hide token
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () {
                initBatch(_serverController.text, _tokenController.text);
              },
              child: const Text("Run"),
            ),
            const SizedBox(height: 24),
            Text(_result),
          ],
        ),
      ),
    );
  }
}

class DownloadScreen extends StatefulWidget {
  final Map<String, int> files;
  final String title;
  final String serverUrl;
  final int threadCount;
  final String token;

  const DownloadScreen({
    super.key,
    required this.files,
    required this.title,
    required this.serverUrl,
    required this.threadCount,
    required this.token,
  });

  @override
  State<DownloadScreen> createState() => _DownloadScreenState();
}

class _DownloadScreenState extends State<DownloadScreen> {
  int downloaded = 0;

  @override
  void initState() {
    super.initState();
    _startDownload();
  }

  void _startDownload() {
    downloadFilesInBatches(widget.serverUrl, widget.files, (count) {
      setState(() {
        downloaded = count;
      });
    }).then((_) {
      if (mounted) {
        Navigator.pop(context);
      }
    });
  }

  Future<void> downloadFilesInBatches(
    String serverUrl,
    Map files,
    void Function(int) onProgress,
  ) async {
    final saveDir = await getSaveDir();
    int completed = 0;
    final queue = List<MapEntry<String, int>>.from(files.entries);
    final futures = <Future>[];

    Future<void> downloadNext() async {
      if (queue.isEmpty) return;
      final entry = queue.removeAt(0);
      final fileName = entry.key;
      final expectedCrc = entry.value;
      final isStage = widget.title.contains("Stages");
      final fileUrl = isStage
          ? "${widget.serverUrl}/files/gc2/${widget.token}/stage/$fileName"
          : "${widget.serverUrl}/files/gc2/${widget.token}/audio/$fileName";
      final file = File("$saveDir$fileName");

      bool valid = false;
      if (await file.exists()) {
        final bytes = await file.readAsBytes();
        final crc = getCrc32(bytes);
        if (crc == expectedCrc) {
          valid = true;
        }
      }

      if (!valid) {
        final response = await http.get(Uri.parse(fileUrl));
        if (response.statusCode == 200) {
          await file.create(recursive: true);
          await file.writeAsBytes(response.bodyBytes);
          // Check CRC after download
          final crc = getCrc32(response.bodyBytes);
          if (crc != expectedCrc) {
            // If CRC still doesn't match, show warning and continue
            if (mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text(
                    "Warning: Checksum failed for $fileName, continuing...",
                  ),
                  backgroundColor: Colors.orange,
                  duration: const Duration(seconds: 2),
                ),
              );
            }
            completed++;
            onProgress(completed);
            await downloadNext();
            return;
          }
        }
      }
      completed++;
      onProgress(completed);
      await downloadNext();
    }

    // Start initial pool
    for (int i = 0; i < widget.threadCount && i < files.length; i++) {
      futures.add(downloadNext());
    }
    await Future.wait(futures);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(widget.title),
            const SizedBox(height: 24),
            LinearProgressIndicator(
              value: widget.files.isEmpty
                  ? 0
                  : downloaded / widget.files.length,
            ),
            const SizedBox(height: 16),
            Text('Downloaded $downloaded / ${widget.files.length} files'),
            const Text(
              "Do not leave this screen while downloading",
              style: TextStyle(color: Colors.red),
            ),
          ],
        ),
      ),
    );
  }
}
