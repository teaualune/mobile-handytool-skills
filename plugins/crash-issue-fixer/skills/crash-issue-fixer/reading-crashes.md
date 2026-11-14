# Reading crash reports

A reference for phase 2. These are leads, not verdicts: confirm each one in the code.

## Symbols

Unreadable app frames make the cause guesswork. What unreadable frames look like, and what fixes them:

| Platform | Looks like | Fix |
|---|---|---|
| iOS | App-binary frames shown as addresses or `<AppBinary> + 123456`; Crashlytics warns about a missing dSYM | Upload that build's dSYM, using Crashlytics' `upload-symbols` script or the build phase. The dSYM comes from the build's archive. |
| Android (Java/Kotlin) | Short obfuscated names: `a.b.c`, `o.xy`, `ab.c(SourceFile)` | Upload the R8/ProGuard mapping file for that build. The Crashlytics Gradle plugin does it when `mappingFileUploadEnabled` is on. |
| Android (NDK) | `.so` frames with addresses only | Upload native symbols (the Crashlytics Gradle plugin's `uploadCrashlyticsSymbolFile<Variant>` task). |
| Flutter | Address-only Dart frames (`abs … virt …`) from any build made with `--split-debug-info`, with or without `--obfuscate`; obfuscated names as well when `--obfuscate` is on | Android: upload the `--split-debug-info` directory with `firebase crashlytics:symbols:upload --app=<App ID> <dir>`. iOS: the Dart symbols go up inside the dSYM (Flutter 3.12+ with `firebase_crashlytics` 3.3.4+), so upload that build's dSYM. |
| React Native | Minified JS function names, or Hermes bytecode offsets, in the exception message | Crashlytics doesn't apply JS source maps. Symbolicate with that release's source map (`metro-symbolicate`) if the caller has it; otherwise rely on names that survive minification, such as component names and string literals. |

Symbols must match the exact build that crashed. Symbols for a different build of the same version are wrong.

## Whose frame

**The app frame** is the first frame, from the top, that belongs to this repo's code:

- **iOS:** frames from the app binary, its own frameworks or its extensions. Not app code: `UIKitCore`, `Foundation`, `CoreFoundation`, `libobjc`, `libswiftCore`, `libdispatch`, `libsystem_*`, and third-party frameworks (check `Podfile.lock` and `Package.resolved`).
- **Android:** classes under the app's own packages (`namespace` / `applicationId` and module packages). Not app code: `android.*`, `androidx.*`, `java.*`, `kotlin.*`, `kotlinx.*`, `com.google.*` (unless the app lives there), or SDK packages (check the Gradle dependencies).

A crash entirely inside system frames usually still has an app cause. Walk down the stack to the deepest app frame that called in: our view's layout pass, an adapter that reports inconsistent counts, a callback we registered. If there is no app frame anywhere, look at what the app did just before, using the breadcrumbs, logs and other threads.

## iOS crash kinds

| Seen as | Usually means | Look at |
|---|---|---|
| `EXC_BREAKPOINT` / `SIGTRAP`, Swift frame on top | A Swift runtime trap: force-unwrap of `nil`, `as!` failure, index out of range, `try!`, `fatalError` / `precondition`, integer overflow | The exact line of the top app frame. Ask why the value can be that way in the field. |
| `_dispatch_assert_queue_fail`, `swift_task_isCurrentExecutor…` frames | An actor-isolation check failed: code isolated to the main actor ran on another queue. Often a callback from an Objective-C API or an SDK that is delivered on a background queue. | Which closure is isolated, and where the caller invokes it |
| `Fatal Exception: NS…` / `EXC_CRASH (SIGABRT)` with a reason | An uncaught Objective-C exception: `NSInvalidArgumentException` (nil in a collection, unrecognized selector), `NSRangeException`, `NSInternalInconsistencyException` (table or collection view batch updates that don't match the data source, UI work off the main thread), `NSGenericException` (collection mutated while enumerated) | The reason string, then the frames where the exception was thrown, not the abort machinery |
| `EXC_BAD_ACCESS` / `SIGSEGV` / `SIGBUS` | Invalid memory access: an object used after release, a data race on unsynchronized state, `unowned` / `Unmanaged` / unsafe-pointer misuse, a C or C++ bug | With `objc_msgSend`, `objc_retain` or `swift_retain` on top: a released object. Which object, which threads touch it, and what releases it. |
| `0x8badf00d` | Watchdog: the main thread was unresponsive too long during launch, resume or a background transition | What the main thread was doing: synchronous I/O or networking, lock waits, heavy work at launch |
| `0xdead10cc` | Suspended while holding a file or SQLite lock in a shared container | Database or file work around backgrounding, especially in app-group containers |
| Memory (jetsam) | Killed for memory; no stack points at the cause | Memory growth from images, caches or leaks. Events skew to low-RAM devices. |

## Android crash kinds

**Exceptions:** read the **last** `Caused by:` first; it is the root. The top exception is often a wrapper, such as `RuntimeException: Unable to start activity` or `InvocationTargetException`.

| Exception | Usually means |
|---|---|
| `NullPointerException` | Kotlin `!!`, a Java platform type assumed non-null, or state lost after process death (see §Skews) |
| `UninitializedPropertyAccessException` | A `lateinit` read before it was set, often after process death or from a callback that arrives early |
| `IllegalStateException: Fragment … not attached to a context` | `requireContext()` / `requireActivity()` in an async callback that outlived the fragment |
| `IllegalStateException: Can not perform this action after onSaveInstanceState` | A fragment transaction or dialog after the state was saved |
| `WindowManager$BadTokenException` | A dialog or popup shown on a finishing or destroyed activity |
| `TransactionTooLargeException` | An oversized `Bundle`: saved state, intent extras or binder payloads |
| `ConcurrentModificationException` | A collection mutated during iteration, often from another thread |
| `CalledFromWrongThreadException` | A view touched off the main thread |
| `ForegroundServiceStartNotAllowedException` (Android 12+) | A foreground service started from the background |
| `ForegroundServiceDidNotStartInTimeException`, or `RemoteServiceException` "did not then call startForeground" | `startForegroundService()` without `startForeground()` in time |
| `MissingForegroundServiceTypeException` (target SDK 34+) | A foreground service without a declared type |
| `SecurityException` | A permission revoked or not granted on that OS version, receiver export flags (target SDK 34+), or a component not exported |
| `IllegalArgumentException` about `FLAG_IMMUTABLE` / `FLAG_MUTABLE` (target SDK 31+) | A `PendingIntent` created without a mutability flag |
| `OutOfMemoryError` | The allocation that failed, which isn't necessarily what used the memory. Look for bitmaps, caches and leaks. |
| `DeadObjectException`, `DeadSystemException` | The remote process or the system died. Often noise around shutdown or updates; check the volume before acting. |

**ANRs** have no exception. Crashlytics records them on Android 11+. The main-thread stack is a snapshot taken at the timeout:

- **Blocked:** I/O, a database, a `synchronized` or lock wait ("waiting to lock … held by thread N": find thread N among all threads), a binder call, `SharedPreferences` commits, or `QueuedWork` waits during `onPause` / `onStop`.
- **Idle in `MessageQueue.nativePollOnce`:** the block was over by the time the snapshot was taken. Look across events and variants, and at broadcast receiver or service timeouts.

**Native (NDK) crashes:** `SIGSEGV` or `SIGABRT` in `.so` frames. Decide whose library it is: the app's own, a third-party SDK's, or the system's (`libc`, `libart`, `libhwui`). Then look at the Java frames below it, which show the JNI caller.

## React Native

- **JS errors:**
  - **iOS:** the native stack shows the reporting machinery (`RCTFatal`, `RCTExceptionsManager`).
  - **Android:** the crash appears as `com.facebook.react.common.JavascriptException`.
  - The real stack is the JS one inside the exception message, so read that. JS errors recorded as non-fatals (e.g. `recordError` in `@react-native-firebase/crashlytics`) carry a JS stack too.
- **Native module crashes:** frames under the module method that JS invoked (`RCTModuleMethod`, `JavaMethodWrapper.invoke`, TurboModule frames in `facebook::react::…`). That method is the app frame if the module is ours. Check what JS passes it: null or undefined arguments, calls after unmount, or UI work on the module's background queue.
- **Libraries:** native code under `node_modules/<lib>/ios` or `/android` is a dependency. Get the version from the lockfile and check the library's issue tracker.
- **New Architecture** (Fabric, TurboModules, JSI): C++ frames in `facebook::react` or `hermes` are often framework-level. Check the issue against the React Native version's known problems before assuming an app fault.

## Flutter

- **Dart exceptions** don't kill the process. They are reported as non-fatal unless the app records them as fatal (`FirebaseCrashlytics.instance.recordFlutterFatalError` in `FlutterError.onError`, or `PlatformDispatcher.instance.onError` with `fatal: true`). Their stack is a Dart stack: `package:<app_package>/…` frames are app code, and `package:flutter/…` frames are the framework.
- **Engine crashes:** native crashes in `Flutter.framework` (iOS) or `libflutter.so` (Android). Check the Flutter version (`pubspec.lock`, `.fvmrc`, CI config) against Flutter's issue tracker. App-side triggers include platform views, very large images and isolate misuse.
- **Plugins:** native frames in plugin code (plugin packages, `io.flutter.plugins.*`, plugin pods) are a dependency. Get the version from `pubspec.lock`.
  - `MissingPluginException`: the plugin isn't registered for that engine, typically in a background isolate or an add-to-app setup.
  - `PlatformException`: the native side returned an error; read the native handler.

## Skews

| Skew | Lead |
|---|---|
| One OS version | That version's behaviour changes for the app's target SDK, or an OS bug |
| One device maker (Samsung, Xiaomi, …) | A vendor customization; usually a workaround or `no-action` |
| Starts at one app version | Diff that release against the previous one |
| Background, or right after launch | Lifecycle: state restoration, cold start, Android process death (activities recreated with saved state while singletons and statics are empty) |
| Low free memory or disk | Memory or disk-full handling |
| Few users, many events | One device or account in a crash loop; look at user IDs and custom keys |
| Rooted, jailbroken, emulators, sideloaded builds | A `no-action` candidate |
| Tablets, foldables, split-screen | Configuration changes and layout assumptions |
