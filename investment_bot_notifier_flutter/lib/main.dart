import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/services.dart';
import 'firebase_options.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:device_info/device_info.dart';

const String keyFulfilledOrders = "fulfilled_orders";
const String keyOrderTitle = "title";
const String keyOrderBody = "body";
const String keyOrderDate = "date";

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Demo',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: const MyHomePage(title: 'DCA Investment Bot'),
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({Key? key, required this.title}) : super(key: key);

  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  final FirebaseMessaging _firebaseMessaging = FirebaseMessaging.instance;

  @override
  void initState() {
    super.initState();

    _firebaseMessaging.getToken().then((token) async {
      if (token == null) return;

      final DeviceInfoPlugin deviceInfoPlugin = DeviceInfoPlugin();
      String identifier = "";
      try {
        if (Platform.isAndroid) {
          var build = await deviceInfoPlugin.androidInfo;
          identifier = build.androidId; //UUID for Android
        } else if (Platform.isIOS) {
          var data = await deviceInfoPlugin.iosInfo;
          identifier = data.identifierForVendor; //UUID for iOS
        }
      } on PlatformException {
        if (kDebugMode) {
          print('Failed to get platform version');
        }
      }

      if (kDebugMode) {
        print('MESSAGING TOKEN IS: ' + token);
      }

      FirebaseFirestore.instance
          .collection("notification_ids")
          .doc(identifier)
          .set({"messaging_token": token});
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title),
      ),
      body: Center(
        child: FutureBuilder(
          future: getLastOrders(),
          builder: (context,
              AsyncSnapshot<QuerySnapshot<Map<String, dynamic>>> snapshot) {
            if (!snapshot.hasError && snapshot.hasData) {
              var docs = snapshot.data!.docs;
              docs.sort((a, b) {
                var dateA = DateTime.tryParse(a.get(keyOrderDate));
                var dateB = DateTime.tryParse(b.get(keyOrderDate));
                if (dateA != null && dateB != null) {
                  return dateB.compareTo(dateA);
                }
                return 0;
              });
              List<Order> items = docs
                  .map((e) => Order(e.get(keyOrderTitle), e.get(keyOrderBody)))
                  .toList();
              return ListView.builder(
                itemCount: items.length,
                itemBuilder: (BuildContext context, int index) {
                  String title = items[index].title;
                  String body = items[index].body;
                  List<String> parts = body.split("|");
                  return Card(
                    elevation: 2,
                    color: HSVColor.fromAHSV(
                            1, getHueValueForCharacters(title), 1, 1)
                        .toColor(),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(title),
                        ListView.builder(
                          physics: const NeverScrollableScrollPhysics(),
                          shrinkWrap: true,
                          itemCount: parts.length,
                          itemBuilder: (context, index) {
                            return Text(parts[index]);
                          },
                        ),
                      ],
                    ),
                  );
                },
              );
            } else {
              return const Text("Error retrieving data from firebase");
            }
          },
        ),
      ),
    );
  }

  Future<QuerySnapshot<Map<String, dynamic>>> getLastOrders() async {
    FirebaseFirestore firestore = FirebaseFirestore.instance;
    var ordersSnapshot = await firestore.collection(keyFulfilledOrders).get();
    return ordersSnapshot;
  }
}

double getHueValueForCharacters(String word) {
  // Takes the characters and sums their codeUnit up, then modolus 360 to get a valid hue value
  double sum = 0;
  word = word.toLowerCase();
  for (var char in word.codeUnits) {
    sum += char;
  }
  return sum % 360;
}

class Order {
  final String title;
  final String body;

  Order(this.title, this.body);
}
