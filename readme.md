### Для доступа через интернет:

https://6gl133cf-8000.uks1.devtunnels.ms + эндпоинт

https://6gl133cf-8000.uks1.devtunnels.ms/api - базовый эндпоинт

---
### Телеграмм
    
[FiveChromoClinicBot](https://t.me/FiveChromoClinicBot)

---

### Пример запроса

curl -X POST -H "Content-Type: application/json" -d "{\"question\":\"Сколько стоит рентген?\"}" https://6gl133cf-8000.uks1.devtunnels.ms/qa

![картинка](picture.jpg)

---

### Локальный запуск:
* в каталоге \bot 
    
    запустить main.py - api бота
* в каталоге \mesengers
  
    запустить telegram_aiohttp.py - оброботчик сообщений из ТГ
* в каталоге \feedback_service
  
    запустить main.py - api сервиса обработки отзывов
<<<<<<< HEAD
* ну и БДшка локальная нужна, создать можно при помощи feedback_service\script.sql
=======
* ну и БДшка локальная нужна, создать можно при помощи feedback_service\script.sql
>>>>>>> 84e1521e108625e7393c5974bdf918f9de8c354b
