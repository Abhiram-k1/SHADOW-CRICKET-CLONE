import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../models/analysis_result.dart';

class ApiService {
  final String baseUrl = "http://localhost:8000/api/v1"; // Update to actual backend URL when deployed

  Future<AnalysisResult> uploadImage(File imageFile) async {
    var uri = Uri.parse("$baseUrl/analyses/");
    var request = http.MultipartRequest('POST', uri);

    request.files.add(await http.MultipartFile.fromPath('file', imageFile.path));
    // Provide a dummy test user header since auth is mocked for V1
    request.headers.addAll({
      'x-user-id': '4a76541c-6c7f-4a8f-bcfd-210c72abe84b'
    });

    var streamedResponse = await request.send();
    var response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 201) {
      return AnalysisResult.fromJson(jsonDecode(response.body));
    } else {
      throw Exception("Failed to upload image: ${response.body}");
    }
  }

  Future<AnalysisResult> getAnalysis(String id) async {
    var uri = Uri.parse("$baseUrl/analyses/$id");
    var response = await http.get(uri, headers: {
      'x-user-id': '4a76541c-6c7f-4a8f-bcfd-210c72abe84b'
    });

    if (response.statusCode == 200) {
      return AnalysisResult.fromJson(jsonDecode(response.body));
    } else {
      throw Exception("Failed to fetch analysis");
    }
  }
}
