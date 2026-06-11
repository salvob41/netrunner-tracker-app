const { withAndroidManifest } = require('expo/config-plugins');

/**
 * Strips Android permissions that get auto-merged in from library manifests
 * (expo-file-system, expo-image, react-native debug overlay, Play licensing)
 * but that this fully-offline tracker app never uses.
 *
 * We keep only the two we actually declare in app.json:
 *   - WAKE_LOCK  (expo-keep-awake: keep screen on during a game)
 *   - VIBRATE    (expo-haptics: tap/token feedback)
 *
 * Removal works via the Android manifest merger's `tools:node="remove"`
 * directive, which deletes the permission contributed by any dependency.
 *
 * Note: dev via `npx expo start` / Expo Go is unaffected — Expo Go is a
 * separate app with its own INTERNET permission, so the production manifest
 * can safely drop it.
 */
const PERMISSIONS_TO_REMOVE = [
  'android.permission.INTERNET',
  'android.permission.ACCESS_NETWORK_STATE',
  'android.permission.READ_EXTERNAL_STORAGE',
  'android.permission.WRITE_EXTERNAL_STORAGE',
  'android.permission.SYSTEM_ALERT_WINDOW',
  'com.android.vending.CHECK_LICENSE',
];

module.exports = function withTrimmedAndroidPermissions(config) {
  return withAndroidManifest(config, (cfg) => {
    const manifest = cfg.modResults.manifest;

    // Ensure the `tools` namespace is declared on <manifest>.
    manifest.$ = manifest.$ || {};
    manifest.$['xmlns:tools'] = 'http://schemas.android.com/tools';

    manifest['uses-permission'] = manifest['uses-permission'] || [];

    // Drop any existing declarations for these permissions, then add an
    // explicit remove directive so library-provided ones are stripped too.
    manifest['uses-permission'] = manifest['uses-permission'].filter(
      (perm) => !PERMISSIONS_TO_REMOVE.includes(perm?.$?.['android:name'])
    );

    for (const name of PERMISSIONS_TO_REMOVE) {
      manifest['uses-permission'].push({
        $: {
          'android:name': name,
          'tools:node': 'remove',
        },
      });
    }

    return cfg;
  });
};
