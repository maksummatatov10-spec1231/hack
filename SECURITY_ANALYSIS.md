# 🔍 Анализ безопасности APK: File Manager+ v3.8.2

## 📋 Основная информация

| Параметр | Значение |
|----------|----------|
| Package | `com.alphainventor.filemanager` |
| Version | 3.8.2 (code: 2103082) |
| Min SDK | 21 (Android 5.0) |
| Target SDK | 35 (Android 15) |
| DEX-файлы | 4 |
| Всего классов | ~26,171 |
| Обфускация | ~40% классов имеют короткие имена (ProGuard/R8) |

---

## 🔐 Найденные уязвимости

### 1. ⚠ JavaScript включен в WebView (СРЕДНИЙ РИСК)

**Где:** `WebViewActivity.setUpWebView()`

```java
this.mWebView.getSettings().setJavaScriptEnabled(1);
```

**Проблема:** WebView загружает внешние URL с включённым JavaScript. Это открывает возможность для XSS-атак, если злоумышленник может контролировать URL, который загружается.

**Рекомендация:** Отключить JavaScript если не нужен, или добавить строгий Content Security Policy.

---

### 2. ⚠ Множество экспортированных компонентов (СРЕДНИЙ РИСК)

**Найдено 14+ экспортированных Activity:**

| Activity | Intent Filter | Риск |
|----------|--------------|------|
| `LaunchActivity` | `VIEW`, `VIEW_DOWNLOADS` | Может быть вызвана извне для открытия файлов |
| `ArchiveActivity` | `VIEW` | Открытие архивов извне |
| `TextEditorActivity` | `VIEW` | Редактирование файлов |
| `VideoPlayerActivity` | `VIEW` | Воспроизведение видео |
| `SaveToActivity` | `SEND`, `SEND_MULTIPLE` | Приём файлов от других приложений |
| `WallpaperActivity` | `ATTACH_DATA` | Установка обоев |
| `SplitApkInstallerActivity` | `VIEW` | Установка APK! |
| `PickerActivity` | `GET_CONTENT`, `OPEN_DOCUMENT` | Выбор файлов |
| `MSURLLauncherActivity` | `VIEW` | Открытие URL |

**Проблема:** Слишком много компонентов доступно извне. В частности, `SplitApkInstallerActivity` с фильтром `VIEW` на APK-файлы — потенциально опасно.

---

### 3. ⚠ FTP-сервер с паролем через Intent (СРЕДНИЙ РИСК)

**Где:** `FtpServerService`

```java
// Пароль передаётся через Intent extras:
this.m0 = p3.getStringExtra("extra_password");
this.l0 = p3.getIntExtra("extra_port_number", 0);
this.q0 = p3.getStringExtra("extra_ip_address");
```

**Проблема:** Пароль FTP передаётся в открытом виде через Intent. Другое приложение с доступом к тем же extras может перехватить пароль.

**Формат URL:** `ftp://%s:%d`

---

### 4. ⚠ Dropbox OAuth в WebView (СРЕДНИЙ РИСК)

**Где:** `WebViewActivity`

```java
this.mDropboxKey = this.getString(2131951918); // ID ресурса
```

**Проблема:** OAuth-авторизация Dropbox происходит через WebView. Это менее безопасно, чем использование Chrome Custom Tabs или нативного SDK. WebView уязвим к перехвату через `shouldOverrideUrlLoading`.

---

### 5. ⚡ Встроенный HTTP-сервер (ВЫСОКИЙ РИСК)

**Где:** `HttpServerService`

Сервис запускает HTTP-сервер на устройстве, используя NanoHTTPD. Это позволяет:
- Получать доступ к файлам на устройстве через браузер
- Потенциально открывает файловую систему локальной сети

**Проблема:** Если сервер запущен в открытой WiFi-сети, любой может получить доступ к файлам.

---

### 6. ⚡ Команда `CommandService` (ВЫСОКИЙ РИСК)

**Где:** `CommandService`

Сервис с названием, подразумевающим выполнение команд. Требует детальнейшего анализа, но потенциально позволяет выполнять произвольные команды на устройстве.

---

### 7. 📡 Обширные разрешения (ИНФОРМАЦИОННЫЙ)

**21 разрешение, включая:**

| Разрешение | Зачем нужно | Риск |
|-----------|-------------|------|
| `INTERNET` | Облачные сервисы | Ожидаемо |
| `READ/WRITE_EXTERNAL_STORAGE` | Файловый менеджер | Ожидаемо |
| `REQUEST_INSTALL_PACKAGES` | Установка APK | ⚠ Позволяет устанавливать приложения |
| `GET_ACCOUNTS` | Авторизация | ⚠ Доступ к аккаунтам |
| `WAKE_LOCK` | Фоновые операции | Низкий |
| `RECEIVE_BOOT_COMPLETED` | Автозапуск | ⚠ Запуск при загрузке |
| `MANAGE_EXTERNAL_STORAGE` | Полный доступ к файлам | ⚠ Очень широкое |
| `QUERY_ALL_PACKAGES` | Список всех приложений | ⚠ Слежка |
| `BILLING` | Google Play Billing | Покупки |

---

### 8. 🔑 Встроенные сертификаты и ключи

**Найдено в APK:**
- `com/google/api/client/googleapis/google.jks` (71 KB Java KeyStore)
- `com/google/api/client/googleapis/google.p12` (P12 сертификат)
- `res/raw/license_server_public_key.der` (лицензионный ключ)
- `assets/digicert_global_g2.cer` (корневой сертификат)

**Проблема:** Встраивание ключей в APK позволяет извлечь их через декомпиляцию.

---

### 9. ☁ Облачные интеграции

| Сервис | Класс-хелпер | Протокол |
|--------|-------------|----------|
| Dropbox | `k` (обфусцирован) | OAuth2 + REST API |
| Google Drive | `OneDriveFileHelper` | OAuth2 + Drive API v3 |
| OneDrive | MSAL | OAuth2 |
| Box | Box SDK | OAuth2 |
| pCloud | pCloud SDK | OAuth2 + WebDAV |
| Yandex Disk | WebDAV | OAuth2 + WebDAV |

**Все сервисы используют OAuth2** — ключи хранятся в ресурсах приложения.

---

### 10. 📊 Firebase Analytics + AdMob

**Конфигурация:**
- Firebase project: `file-manager-plus-65d18`
- Firebase URL: `https://file-manager-plus-65d18.appspot.com/`
- AdMob интеграция с Google Ads Services

**Проблема:** Сбор аналитики и показ рекламы. Трекинг через `ACCESS_ADSERVICES_AD_ID`.

---

## 🎯 Что можно "взломать" (для тестирования)

### Сценарий 1: Перехват FTP-сессии
```
1. Запустить FTP-сервер в приложении
2. Подключиться к тому же WiFi
3. Перехватить трафик (FTP — незашифрованный протокол)
4. Получить доступ ко всем файлам
```

### Сценарий 2: Атака через WebView
```
1. Отправить intent с вредоносным URL на WebViewActivity
2. JavaScript включён → выполнение произвольного JS
3. Через shouldOverrideUrlLoading можно редиректить
```

### Сценарий 3: Экспортация компонентов
```
1. Любой app может вызвать SplitApkInstallerActivity
2. Отправить intent с malicious APK
3. Пользователь может случайно установить вредоносный APK
```

### Сценарий 4: HTTP-сервер
```
1. Запустить HTTP-сервер в приложении
2. В открытой WiFi-сети — доступ к файлам через браузер
3. Возможен directory traversal если нет фильтрации путей
```

---

## 🛡 Рекомендации по исправлению

1. **WebView:** Добавить whitelist доменов, отключить JS если не нужен
2. **Экспортированные компоненты:** Убрать экспорт для `SplitApkInstallerActivity`, добавить `android:permission` для敏感ных Activity
3. **FTP-сервер:** Использовать FTPS (с TLS), не передавать пароль через Intent
4. **HTTP-сервер:** Добавить аутентификацию, ограничить доступ только localhost
5. **Разрешения:** Убрать `QUERY_ALL_PACKAGES`, ограничить `MANAGE_EXTERNAL_STORAGE`
6. **Ключи:** Использовать Android Keystore вместо встраивания ключей в APK
7. **Обфускация:** Увеличить уровень обфускации (сейчас 40%)
8. **Network Security Config:** Убедиться что `cleartextTraffic` запрещён

---

*Анализ выполнен с помощью Androguard 3.3.5, Python 3.11*
*Дата: 5 августа 2026*
