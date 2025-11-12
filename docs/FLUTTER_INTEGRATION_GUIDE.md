# SANGKURIANG Flutter Integration Guide

## Overview

This guide explains how to integrate the SANGKURIANG API with your Flutter application for Indonesian cryptographic project funding and auditing platform.

## Prerequisites

- Flutter SDK (latest stable version)
- Dart SDK (latest stable version)
- Android Studio / Xcode for mobile development
- Basic understanding of REST APIs and JSON

## Installation

### 1. Add Dependencies

Add these dependencies to your `pubspec.yaml`:

```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # HTTP requests
  http: ^1.1.0
  
  # State management
  provider: ^6.1.1
  
  # Local storage
  shared_preferences: ^2.2.2
  flutter_secure_storage: ^9.0.0
  
  # JSON serialization
  json_annotation: ^4.8.1
  
  # Environment configuration
  flutter_dotenv: ^5.1.0
  
  # Image handling
  cached_network_image: ^3.3.0
  
  # Payment integration
  webview_flutter: ^4.4.2
  
  # Local notifications
  flutter_local_notifications: ^16.2.0
  
  # Biometric authentication
  local_auth: ^2.1.6
  
  # QR Code generation
  qr_flutter: ^4.2.0
  
  # URL launcher
  url_launcher: ^6.2.2

dev_dependencies:
  build_runner: ^2.4.7
  json_serializable: ^6.7.1
```

### 2. Environment Configuration

Create a `.env` file in your project root:

```env
# API Configuration
API_BASE_URL=https://api.sangkuriang.id/api/v1
API_TIMEOUT=30000

# Development/Sandbox
DEV_API_BASE_URL=https://sandbox-api.sangkuriang.id/api/v1

# Payment Configuration
MIDTRANS_CLIENT_KEY=your_midtrans_client_key
XENDIT_PUBLIC_KEY=your_xendit_public_key

# App Configuration
APP_NAME=SANGKURIANG
APP_VERSION=1.0.0
SUPPORTED_LOCALES=id,en
```

## Project Structure

```
lib/
├── config/
│   ├── app_config.dart
│   ├── app_theme.dart
│   └── app_routes.dart
├── models/
│   ├── user_model.dart
│   ├── project_model.dart
│   ├── audit_model.dart
│   └── payment_model.dart
├── services/
│   ├── api_service.dart
│   ├── storage_service.dart
│   ├── payment_service.dart
│   └── notification_service.dart
├── providers/
│   ├── auth_provider.dart
│   ├── project_provider.dart
│   └── audit_provider.dart
├── screens/
│   ├── auth/
│   ├── main/
│   ├── projects/
│   └── profile/
└── widgets/
    ├── project_card.dart
    ├── audit_badge.dart
    └── payment_widget.dart
```

## Implementation

### 1. API Service Configuration

Create `lib/services/api_service.dart`:

```dart
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:flutter_dotenv/flutter_dotenv.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  String get baseUrl => dotenv.env['API_BASE_URL'] ?? '';
  String get devBaseUrl => dotenv.env['DEV_API_BASE_URL'] ?? '';
  
  String? _authToken;
  bool _isDevMode = false;

  void setAuthToken(String token) {
    _authToken = token;
  }

  void clearAuthToken() {
    _authToken = null;
  }

  void setDevMode(bool isDev) {
    _isDevMode = isDev;
  }

  Map<String, String> get _headers {
    final headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'X-App-Version': dotenv.env['APP_VERSION'] ?? '1.0.0',
    };

    if (_authToken != null) {
      headers['Authorization'] = 'Bearer $_authToken';
    }

    return headers;
  }

  String get _currentBaseUrl => _isDevMode ? devBaseUrl : baseUrl;

  // GET request
  Future<ApiResponse> get(String endpoint, {Map<String, dynamic>? queryParams}) async {
    try {
      final uri = Uri.parse('$_currentBaseUrl$endpoint').replace(
        queryParameters: queryParams?.map((k, v) => MapEntry(k, v.toString())),
      );

      final response = await http.get(
        uri,
        headers: _headers,
      ).timeout(Duration(milliseconds: int.parse(dotenv.env['API_TIMEOUT'] ?? '30000')));

      return _handleResponse(response);
    } on SocketException {
      throw ApiException('No internet connection');
    } on TimeoutException {
      throw ApiException('Request timeout');
    } catch (e) {
      throw ApiException('An error occurred: $e');
    }
  }

  // POST request
  Future<ApiResponse> post(String endpoint, {Map<String, dynamic>? body}) async {
    try {
      final response = await http.post(
        Uri.parse('$_currentBaseUrl$endpoint'),
        headers: _headers,
        body: jsonEncode(body),
      ).timeout(Duration(milliseconds: int.parse(dotenv.env['API_TIMEOUT'] ?? '30000')));

      return _handleResponse(response);
    } on SocketException {
      throw ApiException('No internet connection');
    } on TimeoutException {
      throw ApiException('Request timeout');
    } catch (e) {
      throw ApiException('An error occurred: $e');
    }
  }

  // PUT request
  Future<ApiResponse> put(String endpoint, {Map<String, dynamic>? body}) async {
    try {
      final response = await http.put(
        Uri.parse('$_currentBaseUrl$endpoint'),
        headers: _headers,
        body: jsonEncode(body),
      ).timeout(Duration(milliseconds: int.parse(dotenv.env['API_TIMEOUT'] ?? '30000')));

      return _handleResponse(response);
    } on SocketException {
      throw ApiException('No internet connection');
    } on TimeoutException {
      throw ApiException('Request timeout');
    } catch (e) {
      throw ApiException('An error occurred: $e');
    }
  }

  // DELETE request
  Future<ApiResponse> delete(String endpoint) async {
    try {
      final response = await http.delete(
        Uri.parse('$_currentBaseUrl$endpoint'),
        headers: _headers,
      ).timeout(Duration(milliseconds: int.parse(dotenv.env['API_TIMEOUT'] ?? '30000')));

      return _handleResponse(response);
    } on SocketException {
      throw ApiException('No internet connection');
    } on TimeoutException {
      throw ApiException('Request timeout');
    } catch (e) {
      throw ApiException('An error occurred: $e');
    }
  }

  ApiResponse _handleResponse(http.Response response) {
    final statusCode = response.statusCode;
    final body = jsonDecode(response.body);

    if (statusCode >= 200 && statusCode < 300) {
      return ApiResponse.success(body['data'] ?? body);
    } else {
      final error = body['error'] ?? 'Unknown error';
      final message = body['message'] ?? 'An error occurred';
      throw ApiException('$error: $message');
    }
  }
}

class ApiResponse {
  final bool success;
  final dynamic data;
  final String? error;

  ApiResponse.success(this.data) : success = true, error = null;
  ApiResponse.error(this.error) : success = false, data = null;
}

class ApiException implements Exception {
  final String message;
  ApiException(this.message);

  @override
  String toString() => 'ApiException: $message';
}
```

### 2. Authentication Integration

Create `lib/providers/auth_provider.dart`:

```dart
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/storage_service.dart';
import '../models/user_model.dart';

class AuthProvider extends ChangeNotifier {
  final ApiService _apiService = ApiService();
  final StorageService _storageService = StorageService();

  User? _user;
  String? _token;
  bool _isLoading = false;
  String? _error;

  User? get user => _user;
  String? get token => _token;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isAuthenticated => _token != null && _user != null;

  Future<void> initialize() async {
    _token = await _storageService.getToken();
    final userData = await _storageService.getUserData();
    
    if (_token != null && userData != null) {
      _user = User.fromJson(userData);
      _apiService.setAuthToken(_token!);
      notifyListeners();
    }
  }

  Future<bool> login(String email, String password) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      final response = await _apiService.post('/auth/login', body: {
        'email': email,
        'password': password,
      });

      if (response.success) {
        _token = response.data['access_token'];
        _user = User.fromJson(response.data['user']);
        
        await _storageService.setToken(_token!);
        await _storageService.setUserData(_user!.toJson());
        
        _apiService.setAuthToken(_token!);
        
        _isLoading = false;
        notifyListeners();
        return true;
      }
      
      return false;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<bool> register(Map<String, dynamic> userData) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      final response = await _apiService.post('/auth/register', body: userData);

      if (response.success) {
        _token = response.data['access_token'];
        _user = User.fromJson(response.data['user']);
        
        await _storageService.setToken(_token!);
        await _storageService.setUserData(_user!.toJson());
        
        _apiService.setAuthToken(_token!);
        
        _isLoading = false;
        notifyListeners();
        return true;
      }
      
      return false;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    _token = null;
    _user = null;
    _apiService.clearAuthToken();
    
    await _storageService.clearAuthData();
    
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
```

### 3. Payment Integration

Create `lib/services/payment_service.dart`:

```dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'api_service.dart';

class PaymentService {
  final ApiService _apiService = ApiService();

  Future<Map<String, dynamic>> processPayment({
    required String fundingId,
    required String paymentMethod,
    required Map<String, dynamic> paymentDetails,
  }) async {
    try {
      final response = await _apiService.post('/payment/process', body: {
        'funding_id': fundingId,
        'payment_method': paymentMethod,
        'payment_details': paymentDetails,
      });

      if (response.success) {
        return response.data;
      } else {
        throw Exception('Payment processing failed');
      }
    } catch (e) {
      throw Exception('Payment error: $e');
    }
  }

  Future<List<Map<String, dynamic>>> getPaymentMethods() async {
    try {
      final response = await _apiService.get('/payment/methods');
      
      if (response.success) {
        return List<Map<String, dynamic>>.from(response.data);
      } else {
        return [];
      }
    } catch (e) {
      return [];
    }
  }

  Future<Map<String, dynamic>> getTransactionDetails(String transactionId) async {
    try {
      final response = await _apiService.get('/payment/transaction/$transactionId');
      
      if (response.success) {
        return response.data;
      } else {
        throw Exception('Failed to get transaction details');
      }
    } catch (e) {
      throw Exception('Transaction error: $e');
    }
  }
}

class PaymentWebView extends StatefulWidget {
  final String paymentUrl;
  final Function(Map<String, dynamic>) onSuccess;
  final Function(String) onError;

  const PaymentWebView({
    Key? key,
    required this.paymentUrl,
    required this.onSuccess,
    required this.onError,
  }) : super(key: key);

  @override
  _PaymentWebViewState createState() => _PaymentWebViewState();
}

class _PaymentWebViewState extends State<PaymentWebView> {
  late final WebViewController _controller;

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(
        NavigationDelegate(
          onNavigationRequest: (NavigationRequest request) {
            if (request.url.contains('success')) {
              widget.onSuccess({'status': 'success'});
              Navigator.pop(context);
              return NavigationDecision.prevent;
            } else if (request.url.contains('cancel')) {
              widget.onError('Payment cancelled');
              Navigator.pop(context);
              return NavigationDecision.prevent;
            }
            return NavigationDecision.navigate;
          },
        ),
      )
      ..loadRequest(Uri.parse(widget.paymentUrl));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Pembayaran'),
        backgroundColor: Colors.red,
      ),
      body: WebViewWidget(controller: _controller),
    );
  }
}
```

### 4. Notification Integration

Create `lib/services/notification_service.dart`:

```dart
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

class NotificationService {
  static final FlutterLocalNotificationsPlugin _notifications = 
      FlutterLocalNotificationsPlugin();

  static Future<void> initialize() async {
    const AndroidInitializationSettings initializationSettingsAndroid =
        AndroidInitializationSettings('@mipmap/ic_launcher');

    const InitializationSettings initializationSettings =
        InitializationSettings(android: initializationSettingsAndroid);

    await _notifications.initialize(
      initializationSettings,
      onDidReceiveNotificationResponse: (NotificationResponse response) {
        // Handle notification tap
        _handleNotificationTap(response.payload);
      },
    );

    // Request permissions
    await FirebaseMessaging.instance.requestPermission();

    // Handle foreground messages
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      _showNotification(message);
    });

    // Handle background messages
    FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
  }

  static Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
    // Handle background message
    print('Handling background message: ${message.messageId}');
  }

  static Future<void> _showNotification(RemoteMessage message) async {
    const AndroidNotificationDetails androidPlatformChannelSpecifics =
        AndroidNotificationDetails(
      'sangkuriang_channel',
      'SANGKURIANG Notifications',
      importance: Importance.high,
      priority: Priority.high,
      showWhen: false,
    );

    const NotificationDetails platformChannelSpecifics =
        NotificationDetails(android: androidPlatformChannelSpecifics);

    await _notifications.show(
      0,
      message.notification?.title ?? 'SANGKURIANG',
      message.notification?.body ?? 'You have a new notification',
      platformChannelSpecifics,
      payload: jsonEncode(message.data),
    );
  }

  static void _handleNotificationTap(String? payload) {
    if (payload != null) {
      final data = jsonDecode(payload);
      // Navigate to relevant screen based on notification data
      print('Notification tapped with payload: $data');
    }
  }

  static Future<void> showLocalNotification({
    required String title,
    required String body,
    String? payload,
  }) async {
    const AndroidNotificationDetails androidPlatformChannelSpecifics =
        AndroidNotificationDetails(
      'sangkuriang_local',
      'SANGKURIANG Local',
      importance: Importance.high,
      priority: Priority.high,
    );

    const NotificationDetails platformChannelSpecifics =
        NotificationDetails(android: androidPlatformChannelSpecifics);

    await _notifications.show(
      DateTime.now().millisecond,
      title,
      body,
      platformChannelSpecifics,
      payload: payload,
    );
  }
}
```

## Usage Examples

### 1. User Authentication

```dart
// Login
final authProvider = Provider.of<AuthProvider>(context, listen: false);
final success = await authProvider.login(email, password);

if (success) {
  Navigator.pushReplacementNamed(context, '/home');
} else {
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(content: Text(authProvider.error ?? 'Login failed')),
  );
}

// Register
final success = await authProvider.register({
  'name': 'John Doe',
  'email': 'john@example.com',
  'password': 'password123',
  'phone': '081234567890',
});
```

### 2. Project Management

```dart
// Get projects
final response = await apiService.get('/projects', queryParams: {
  'page': '1',
  'limit': '10',
  'category': 'cryptography',
});

if (response.success) {
  final projects = List<Project>.from(
    response.data['items'].map((json) => Project.fromJson(json))
  );
  // Update UI with projects
}

// Create project
final response = await apiService.post('/projects', body: {
  'title': 'My Crypto Project',
  'description': 'A secure cryptographic protocol',
  'category': 'cryptography',
  'funding_goal': 50000000,
  'github_url': 'https://github.com/user/project',
});
```

### 3. Payment Processing

```dart
// Process payment
final paymentService = PaymentService();
final paymentData = await paymentService.processPayment(
  fundingId: 'funding123',
  paymentMethod: 'gopay',
  paymentDetails: {
    'phone_number': '081234567890',
  },
);

// Open payment webview
Navigator.push(
  context,
  MaterialPageRoute(
    builder: (context) => PaymentWebView(
      paymentUrl: paymentData['payment_url'],
      onSuccess: (data) {
        // Handle success
      },
      onError: (error) {
        // Handle error
      },
    ),
  ),
);
```

## Best Practices

### 1. Error Handling

Always wrap API calls in try-catch blocks:

```dart
try {
  final response = await apiService.get('/projects');
  // Handle success
} on ApiException catch (e) {
  // Handle API specific errors
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(content: Text(e.message)),
  );
} catch (e) {
  // Handle other errors
  print('Unexpected error: $e');
}
```

### 2. Loading States

Use loading indicators during API calls:

```dart
bool _isLoading = false;

Future<void> fetchProjects() async {
  setState(() => _isLoading = true);
  
  try {
    final response = await apiService.get('/projects');
    // Handle response
  } finally {
    setState(() => _isLoading = false);
  }
}
```

### 3. Token Management

Implement automatic token refresh:

```dart
Future<ApiResponse> _makeAuthenticatedRequest(Future<ApiResponse> request) async {
  try {
    return await request;
  } on ApiException catch (e) {
    if (e.message.contains('Authentication')) {
      // Try to refresh token
      final newToken = await _refreshToken();
      if (newToken != null) {
        // Retry original request with new token
        return await request;
      } else {
        // Navigate to login
        Navigator.pushReplacementNamed(context, '/login');
        rethrow;
      }
    }
    rethrow;
  }
}
```

### 4. Offline Support

Implement offline support using local storage:

```dart
Future<List<Project>> getProjects() async {
  try {
    // Try to fetch from API
    final response = await apiService.get('/projects');
    final projects = List<Project>.from(response.data.map((json) => Project.fromJson(json)));
    
    // Cache for offline use
    await storageService.setCachedProjects(projects.map((p) => p.toJson()).toList());
    
    return projects;
  } catch (e) {
    // Fallback to cached data
    final cachedData = await storageService.getCachedProjects();
    return cachedData.map((json) => Project.fromJson(json)).toList();
  }
}
```

## Testing

### Unit Testing

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import '../lib/services/api_service.dart';

class MockApiService extends Mock implements ApiService {}

void main() {
  group('AuthProvider', () {
    test('should authenticate user successfully', () async {
      final mockApiService = MockApiService();
      final authProvider = AuthProvider();
      
      when(mockApiService.post('/auth/login', any))
          .thenAnswer((_) async => ApiResponse.success({
                'access_token': 'test-token',
                'user': {'id': '1', 'name': 'Test User'},
              }));
      
      final result = await authProvider.login('test@example.com', 'password');
      
      expect(result, true);
      expect(authProvider.isAuthenticated, true);
    });
  });
}
```

### Integration Testing

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:sangkuriang/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  test('complete user flow', () async {
    app.main();
    
    // Test login flow
    await tester.pumpAndSettle();
    
    // Enter credentials
    await tester.enterText(find.byKey(Key('email_field')), 'test@example.com');
    await tester.enterText(find.byKey(Key('password_field')), 'password');
    
    // Tap login button
    await tester.tap(find.byKey(Key('login_button')));
    await tester.pumpAndSettle();
    
    // Verify home screen
    expect(find.text('SANGKURIANG'), findsOneWidget);
  });
}
```

## Deployment

### Android Deployment

1. Update `android/app/build.gradle`:

```gradle
android {
    defaultConfig {
        applicationId "id.sangkuriang.app"
        minSdkVersion 21
        targetSdkVersion 34
        versionCode 1
        versionName "1.0.0"
    }
    
    signingConfigs {
        release {
            storeFile file('sangkuriang.keystore')
            storePassword System.getenv('KEYSTORE_PASSWORD')
            keyAlias 'sangkuriang'
            keyPassword System.getenv('KEY_PASSWORD')
        }
    }
    
    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}
```

2. Build release APK:

```bash
flutter build apk --release
```

### iOS Deployment

1. Update `ios/Runner/Info.plist`:

```xml
<key>CFBundleDisplayName</key>
<string>SANGKURIANG</string>
<key>CFBundleIdentifier</key>
<string>id.sangkuriang.app</string>
<key>CFBundleVersion</key>
<string>1.0.0</string>
```

2. Build for iOS:

```bash
flutter build ios --release
```

## Troubleshooting

### Common Issues

1. **Network Timeout**
   - Check internet connection
   - Verify API endpoint configuration
   - Increase timeout duration

2. **Authentication Errors**
   - Verify token is valid and not expired
   - Check token refresh implementation
   - Ensure proper error handling

3. **Payment Processing Issues**
   - Verify payment gateway configuration
   - Check payment method availability
   - Test with sandbox environment

4. **Build Issues**
   - Update Flutter SDK
   - Clear build cache: `flutter clean`
   - Update dependencies: `flutter pub upgrade`

### Debug Mode

Enable debug mode for detailed logging:

```dart
// In main.dart
void main() {
  if (kDebugMode) {
    // Enable debug logging
    ApiService().setDevMode(true);
  }
  runApp(MyApp());
}
```

## Support

For integration support:
- **Documentation**: https://docs.sangkuriang.id
- **API Support**: support@sangkuriang.id
- **Flutter Community**: https://discord.gg/sangkuriang
- **GitHub Issues**: https://github.com/sangkuriang/flutter-sdk/issues