📄 راهنمای استفاده از build_desktop_offline.bat

این فایل batch به صورت ۱۰۰٪ آفلاین، نسخه اجرایی (exe) دسکتاپ GreenStream را می‌سازد.
برای اجرای آن مراحل زیر را انجام دهید:

1. ساخت پوشه offline packages (فقط یک‌بار روی سیستم آنلاین):
   pip download -d E:\Projects\GreenStream\packages -r E:\Projects\GreenStream\frontend\requirements.txt
   pip download -d E:\Projects\GreenStream\packages pyinstaller

   این کار باعث می‌شود تمام وابستگی‌ها (kivy, requests, pyinstaller و ...) برای نصب آفلاین ذخیره شوند.

2. کپی کردن کل پروژه + فولدر packages به سیستم آفلاین مورد نظر.

3. اجرای فایل build_desktop_offline.bat:
   - محیط مجازی را فعال می‌کند.
   - پکیج‌های لازم را از پوشه packages به‌صورت آفلاین نصب می‌کند.
   - توسط PyInstaller یک فایل exe آفلاین می‌سازد.
   - خروجی را در فولدر release قرار می‌دهد.

4. استفاده از خروجی:
   - فایل `GreenStreamDesktop.exe` در مسیر E:\Projects\GreenStream\release قرار دارد.
   - این فایل به تنهایی در هر سیستم ویندوزی (Win10+) اجرا می‌شود.
   - برای داشتن یک روند نصب حرفه‌ای (Next → Finish + ایجاد آیکون دسکتاپ)، از این فایل exe در ابزار advanced installer استفاده کنید.

⚠ نکته مهم:
- برای پشتیبانی کامل Win7، بیلد را روی سیستم یا VM ویندوز 7 با Python 3.9.13 انجام دهید.
- مطمئن شوید پوشه `assets` و فایل `app_icon.ico` در مسیر صحیح قرار دارند.
