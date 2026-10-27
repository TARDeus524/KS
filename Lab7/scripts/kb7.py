# -*- coding: utf-8 -*-
"""Опис предметної області ЛР7: класи, властивості, індивіди, ситуації, CQ."""

MM = "https://knowledge.uni.lviv.ua/mobility#"
ONT = "https://knowledge.uni.lviv.ua/mobility"
DATA_ONT = "https://knowledge.uni.lviv.ua/mobility/data"
SCHEMA = "https://schema.org/"

CLASSES = {
    "MobilitySystem": ("Інтелектуальна мобільність", None, "Предметна область, що охоплює транспортну систему, дані, учасників і процеси прийняття рішень для управління міською мобільністю.", "ЛР4, ЛР6; Domain Knowledge Hub"),
    "TransportSystem": ("Транспортна система", "MobilitySystem", "Система, що об’єднує транспортну мережу, рухомий склад, рейси, учасників і управлінські процеси міста.", "ЛР4, ЛР6; GTFS Reference 2026"),
    "TransportNetwork": ("Транспортна мережа", "TransportSystem", "Транспортна система, що складається з вузлів, ділянок і маршрутів та утворює граф міста.", "ЛР4, ЛР6; GTFS Reference 2026"),
    "TransportNode": ("Транспортний вузол", "TransportNetwork", "Елемент транспортної мережі, що є зупинкою або пересадочним вузлом і з’єднує ділянки мережі.", "ЛР4, ЛР6"),
    "Stop": ("Зупинка", "TransportNode", "Транспортний вузол, у якому пасажири здійснюють посадку або висадку, а транспортні засоби зупиняються за розкладом.", "GTFS stops.txt; schema:BusStop"),
    "InterchangeStop": ("Пересадочна зупинка", "Stop", "Зупинка, яку обслуговують щонайменше два різні транспортні маршрути і на якій можлива пересадка.", "ЛР4, ЛР6; GTFS transfers.txt"),
    "AccessibleStop": ("Доступна зупинка", "Stop", "Зупинка, обладнана для посадки та висадки маломобільних пасажирів, зокрема з ознакою доступності.", "GTFS stops.txt; schema:BusStop"),
    "NetworkSegment": ("Ділянка мережі", "TransportNetwork", "Частина транспортної мережі між двома сусідніми зупинками, що має час і відстань проходження.", "ЛР5, ЛР6; GTFS shapes.txt"),
    "CongestedSegment": ("Завантажена ділянка", "NetworkSegment", "Ділянка мережі, на якій зафіксовано подію затору, що впливає на час руху.", "ЛР6; GTFS Reference 2026"),
    "TransportRoute": ("Транспортний маршрут", "TransportNetwork", "Упорядкована послідовність зупинок, що обслуговується рейсами під спільним ідентифікатором.", "GTFS routes.txt; schema:Route"),
    "BusRoute": ("Автобусний маршрут", "TransportRoute", "Транспортний маршрут, що обслуговується автобусами і має GTFS route_type = 3.", "GTFS routes.txt"),
    "TramRoute": ("Трамвайний маршрут", "TransportRoute", "Транспортний маршрут, що обслуговується трамваями і має GTFS route_type = 0.", "GTFS routes.txt"),
    "TrolleybusRoute": ("Тролейбусний маршрут", "TransportRoute", "Транспортний маршрут, що обслуговується тролейбусами і має GTFS route_type = 11.", "GTFS routes.txt"),
    "Vehicle": ("Транспортний засіб", "TransportSystem", "Рухомий склад, що виконує рейси на маршрутах і має ідентифікатор та пасажиромісткість.", "ЛР4, ЛР6; GTFS trips.txt"),
    "Bus": ("Автобус", "Vehicle", "Транспортний засіб, що рухається автомобільною дорогою і використовується на автобусних маршрутах.", "GTFS route_type = 3"),
    "Tram": ("Трамвай", "Vehicle", "Рейковий транспортний засіб, що рухається трамвайною колією у міській мережі.", "GTFS route_type = 0"),
    "Trolleybus": ("Тролейбус", "Vehicle", "Транспортний засіб з електроживленням від контактної мережі, що використовується на тролейбусних маршрутах.", "GTFS route_type = 11"),
    "Trip": ("Рейс", "TransportSystem", "Конкретне виконання маршруту в певний час, що складається з послідовності зупинок і зупиночних часів.", "GTFS trips.txt, stop_times.txt"),
    "DelayedTrip": ("Затриманий рейс", "Trip", "Рейс, фактичний стан якого відхилено від розкладу щонайменше на порогову величину затримки.", "ЛР6; SIRI"),
    "Schedule": ("Розклад", "TransportSystem", "План виконання рейсів, що визначає дати, часи та інтервали руху на маршрутах.", "GTFS calendar.txt, frequencies.txt"),
    "ServiceCalendar": ("Календар обслуговування", "Schedule", "Розклад, що визначає множину дат, у які доступне обслуговування маршруту.", "GTFS calendar.txt, calendar_dates.txt"),
    "StopTime": ("Зупиночний час", "Schedule", "Запис розкладу про прибуття або відправлення рейсу на конкретній зупинці.", "GTFS stop_times.txt"),
    "Frequency": ("Інтервал руху", "Schedule", "Запис розкладу про проміжок часу між послідовними відправленнями рейсів на маршруті.", "GTFS frequencies.txt"),
    "Fare": ("Тариф", "TransportSystem", "Правила та вартість оплати проїзду, що застосовуються до маршрутів або поїздок.", "GTFS fare_attributes.txt"),
    "RouteShape": ("Форма маршруту", "TransportSystem", "Геометрія шляху руху транспортного засобу, подана послідовністю координат.", "GTFS shapes.txt"),
    "Actor": ("Учасник процесу", "TransportSystem", "Особа або організація, що бере участь у транспортному процесі та прийнятті рішень.", "ЛР4, ЛР6"),
    "Passenger": ("Пасажир", "Actor", "Учасник процесу, що користується транспортом і здійснює поїздку між зупинками.", "ЛР4, ЛР6; schema:Person"),
    "Driver": ("Водій", "Actor", "Учасник процесу, що керує транспортним засобом під час виконання рейсу.", "ЛР4, ЛР6"),
    "Dispatcher": ("Диспетчер", "Actor", "Учасник процесу, що контролює виконання рейсів і реагує на події в реальному часі.", "ЛР4, ЛР6"),
    "TransportAgency": ("Перевізник", "Actor", "Організація, що надає транспортні послуги, володіє рухомим складом і публікує дані.", "GTFS agency.txt; schema:Organization"),
    "DataAsset": ("Джерело даних", "TransportSystem", "Ресурс, що містить структуровані дані про мережу, рух або пасажирів і використовується аналітикою.", "ЛР4, ЛР6"),
    "GTFSDataset": ("Набір GTFS", "DataAsset", "Джерело даних, що складається з CSV-файлів GTFS для опису маршрутів, рейсів, зупинок і розкладів.", "GTFS Reference 2026"),
    "SIRIFeed": ("Потік SIRI", "DataAsset", "Джерело даних, що містить повідомлення SIRI про рух транспорту в реальному часі.", "SIRI; Transmodel"),
    "NeTExDataset": ("Набір NeTEx", "DataAsset", "Джерело даних, що містить XML-описи мережі, розкладів і тарифів за стандартом NeTEx.", "NeTEx; Transmodel"),
    "Sensor": ("Сенсор", "DataAsset", "Пристрій, що автоматично вимірює стан транспортного процесу та передає дані в систему.", "ЛР4, ЛР6"),
    "GPSTracker": ("GPS-трекер", "Sensor", "Сенсор, що визначає координати, швидкість і час руху транспортного засобу.", "ЛР6; GTFS realtime"),
    "TicketValidator": ("Валідатор квитків", "Sensor", "Сенсор, що фіксує факти валідації квитків і посадки пасажирів на зупинці.", "ЛР6"),
    "PassengerCounter": ("Лічильник пасажирів", "Sensor", "Сенсор, що вимірює кількість пасажирів у транспортному засобі або на зупинці.", "ЛР6"),
    "Analytics": ("Аналітика", "TransportSystem", "Процес обробки даних, що перетворює вимірювання на прогнози, оцінки та рекомендації.", "ЛР4, ЛР6"),
    "Forecast": ("Прогноз", "Analytics", "Аналітичний результат, що оцінює майбутній пасажиропотік, затримку або час у дорозі.", "ЛР6"),
    "DecisionSupport": ("Підтримка рішень", "Analytics", "Аналітичний процес, що поєднує прогнози й правила для вибору управлінської дії.", "ЛР6"),
    "DispatchDecision": ("Диспетчерське рішення", "Analytics", "Аналітичний результат, що визначає управлінську дію диспетчера на подію або відхилення від розкладу.", "ЛР6"),
    "Recommendation": ("Рекомендація", "Analytics", "Аналітичний результат, що пропонує пасажиру або диспетчеру конкретну дію щодо маршруту чи рейсу.", "ЛР6"),
    "Event": ("Подія", "TransportSystem", "Зміна умов транспортного процесу, що виникає в часі та впливає на мережу або рейс.", "ЛР4, ЛР6; schema:Event"),
    "VehicleFailure": ("Поломка транспортного засобу", "Event", "Подія, за якої транспортний засіб не може продовжити виконання рейсу без заміни.", "SIRI; ЛР6"),
    "PassengerSurge": ("Сплеск пасажиропотоку", "Event", "Подія, за якої попит на перевезення різко перевищує плановий пасажиропотік.", "ЛР6; SIRI"),
    "WeatherEvent": ("Погіршення погоди", "Event", "Подія, за якої погодні умови знижують швидкість або надійність руху транспорту.", "SIRI; ЛР6"),
    "Congestion": ("Затор", "Event", "Подія, що спричиняє зниження швидкості руху на ділянці мережі та збільшення затримки.", "ЛР4, ЛР6"),
    "Roadwork": ("Ремонт дороги", "Event", "Подія, що тимчасово обмежує пропускну здатність ділянки мережі через ремонтні роботи.", "ЛР6"),
    "TransportState": ("Стан рейсу", "TransportSystem", "Стан виконання рейсу, що характеризує його відповідність розкладу та завантаженість.", "ЛР6; SIRI"),
    "CrowdedState": ("Стан перевантаження", "TransportState", "Стан рейсу, за якого завантаженість перевищує допустимий рівень комфорту.", "ЛР6; SIRI"),
    "DelayedState": ("Стан затримки", "TransportState", "Стан рейсу, за якого фактичний час виконання перевищує плановий час розкладу.", "ЛР6; SIRI"),
    "OnTimeState": ("Стан за розкладом", "TransportState", "Стан рейсу, за якого фактичний час виконання відповідає плановому часу розкладу.", "ЛР6; SIRI"),
    "Measurement": ("Вимірювання", "TransportSystem", "Кількісна характеристика транспортного процесу, отримана від сенсора або обчислена аналітикою.", "ЛР6"),
    "PassengerFlow": ("Пасажиропотік", "Measurement", "Вимірювання кількості пасажирів, що проходять через зупинку або ділянку за одиницю часу.", "ЛР4, ЛР6"),
    "LoadFactor": ("Завантаженість", "Measurement", "Вимірювання частки використаної місткості транспортного засобу на рейсі.", "ЛР4, ЛР6"),
    "Delay": ("Затримка", "Measurement", "Вимірювання відхилення фактичного часу руху рейсу від планового часу розкладу.", "ЛР4, ЛР6; SIRI"),
    "TravelTime": ("Час у дорозі", "Measurement", "Вимірювання тривалості проходження ділянки або виконання поїздки між зупинками.", "ЛР4, ЛР6"),
}

OBJ_PROPS = {
    "hasPart": ("містить", "MobilitySystem", "MobilitySystem", "inverse:partOf", "Відношення ціле-частина між елементами предметної області."),
    "partOf": ("є частиною", "MobilitySystem", "MobilitySystem", "transitive; inverse:hasPart", "Обернене до hasPart транзитивне відношення належності цілому."),
    "servesStop": ("обслуговує зупинку", "TransportRoute", "Stop", "inverse:servedByRoute", "Маршрут обслуговує зупинку, на якій зупиняються його рейси."),
    "servedByRoute": ("обслуговується маршрутом", "Stop", "TransportRoute", "inverse:servesStop", "Зупинка обслуговується транспортним маршрутом."),
    "hasTrip": ("має рейс", "TransportRoute", "Trip", "inverse:tripOfRoute", "Маршрут містить конкретні рейси, що його виконують."),
    "tripOfRoute": ("є рейсом маршруту", "Trip", "TransportRoute", "inverse:hasTrip", "Рейс належить транспортному маршруту."),
    "startsAt": ("починається на", "Trip", "Stop", "inverse:isStartOf", "Рейс починається на заданій зупинці."),
    "isStartOf": ("є початком", "Stop", "Trip", "inverse:startsAt", "Зупинка є початковою для рейсу."),
    "endsAt": ("завершується на", "Trip", "Stop", "inverse:isEndOf", "Рейс завершується на заданій зупинці."),
    "isEndOf": ("є завершенням", "Stop", "Trip", "inverse:endsAt", "Зупинка є кінцевою для рейсу."),
    "usesVehicle": ("використовує транспортний засіб", "Trip", "Vehicle", "inverse:assignedToTrip", "Рейс виконується конкретним транспортним засобом."),
    "assignedToTrip": ("призначений на рейс", "Vehicle", "Trip", "inverse:usesVehicle", "Транспортний засіб призначено на виконання рейсу."),
    "operatedBy": ("виконується перевізником", "Trip", "TransportAgency", "inverse:operatesTrip", "Рейс виконується транспортним перевізником."),
    "operatesTrip": ("виконує рейс", "TransportAgency", "Trip", "inverse:operatedBy", "Перевізник виконує конкретний рейс."),
    "hasDriver": ("має водія", "Trip", "Driver", "inverse:drivesTrip", "Рейс обслуговує конкретний водій."),
    "drivesTrip": ("керує рейсом", "Driver", "Trip", "inverse:hasDriver", "Водій виконує конкретний рейс."),
    "hasStopTime": ("має зупиночний час", "Trip", "StopTime", "inverse:stopTimeOfTrip", "Рейс містить записи часу прибуття та відправлення на зупинках."),
    "stopTimeOfTrip": ("є часом рейсу", "StopTime", "Trip", "inverse:hasStopTime", "Запис часу зупинки належить конкретному рейсу."),
    "atStop": ("на зупинці", "StopTime", "Stop", "inverse:stopAtTime", "Запис часу зупинки стосується конкретної зупинки."),
    "stopAtTime": ("має запис часу", "Stop", "StopTime", "inverse:atStop", "Зупинка має записи часу прибуття та відправлення."),
    "hasEvent": ("має подію", "NetworkSegment", "Event", "inverse:affectsSegment", "Ділянка мережі має пов’язану подію, що змінює умови руху."),
    "affectsSegment": ("впливає на ділянку", "Event", "NetworkSegment", "inverse:hasEvent", "Подія впливає на конкретну ділянку транспортної мережі."),
    "affectsTrip": ("впливає на рейс", "Event", "Trip", "inverse:affectedByEvent", "Подія спричиняє зміну виконання конкретного рейсу."),
    "affectedByEvent": ("зазнає впливу події", "Trip", "Event", "inverse:affectsTrip", "Рейс зазнає впливу події на мережі."),
    "hasState": ("має стан", "Trip", "TransportState", "inverse:stateOfTrip", "Рейс перебуває в конкретному стані виконання."),
    "stateOfTrip": ("є станом рейсу", "TransportState", "Trip", "inverse:hasState", "Стан описує конкретний рейс."),
    "hasMeasurement": ("має вимірювання", "Trip", "Measurement", "inverse:measurementOf", "Рейс має кількісні вимірювання затримки, завантаженості або часу."),
    "measurementOf": ("є вимірюванням", "Measurement", "Trip", "inverse:hasMeasurement", "Вимірювання стосується конкретного рейсу."),
    "measuredBy": ("виміряне сенсором", "Measurement", "Sensor", "inverse:measures", "Вимірювання отримане конкретним сенсором."),
    "measures": ("вимірює", "Sensor", "Measurement", "inverse:measuredBy", "Сенсор формує конкретне вимірювання."),
    "basedOnForecast": ("ґрунтується на прогнозі", "DecisionSupport", "Forecast", "inverse:supportsDecision", "Рішення використовує конкретний прогноз."),
    "supportsDecision": ("підтримує рішення", "Forecast", "DecisionSupport", "inverse:basedOnForecast", "Прогноз є підставою для управлінського рішення."),
    "hasRecommendation": ("має рекомендацію", "DecisionSupport", "Recommendation", "inverse:recommendationOfDecision", "Рішення породжує конкретну рекомендацію."),
    "recommendationOfDecision": ("є рекомендацією рішення", "Recommendation", "DecisionSupport", "inverse:hasRecommendation", "Рекомендація походить від управлінського рішення."),
    "recommends": ("рекомендує маршрут", "Recommendation", "TransportRoute", "inverse:recommendedBy", "Рекомендація пропонує конкретний маршрут."),
    "recommendedBy": ("рекомендований", "TransportRoute", "Recommendation", "inverse:recommends", "Маршрут пропонується рекомендацією."),
    "forPassenger": ("призначена пасажиру", "Recommendation", "Passenger", "inverse:passengerRecommendation", "Рекомендація адресована конкретному пасажиру."),
    "passengerRecommendation": ("має рекомендацію", "Passenger", "Recommendation", "inverse:forPassenger", "Пасажир отримує конкретну рекомендацію."),
    "respondsTo": ("реагує на подію", "Dispatcher", "Event", "inverse:handledBy", "Диспетчер реагує на подію в реальному часі."),
    "handledBy": ("опрацьована диспетчером", "Event", "Dispatcher", "inverse:respondsTo", "Подія опрацьована конкретним диспетчером."),
    "interchangesWith": ("має пересадку з", "Stop", "Stop", "symmetric", "Симетричне відношення між зупинками, між якими можлива пересадка."),
    "frequencyOfRoute": ("є інтервалом маршруту", "Frequency", "TransportRoute", "inverse:routeFrequency", "Запис інтервалу руху належить конкретному маршруту."),
    "routeFrequency": ("має інтервал", "TransportRoute", "Frequency", "inverse:frequencyOfRoute", "Маршрут має заданий інтервал руху."),
    "datasetDescribes": ("описує мережу", "DataAsset", "TransportNetwork", "inverse:describedByDataset", "Джерело даних описує транспортну мережу."),
    "describedByDataset": ("описана джерелом", "TransportNetwork", "DataAsset", "inverse:datasetDescribes", "Транспортна мережа описана конкретним джерелом даних."),
    "forecastFor": ("прогнозує рейс", "Forecast", "Trip", "inverse:forecastOfTrip", "Прогноз стосується конкретного рейсу."),
    "forecastOfTrip": ("має прогноз", "Trip", "Forecast", "inverse:forecastFor", "Рейс має прогнозне значення."),
    "locatedAt": ("розташована в", "Stop", "schema:Place", "external mapping", "Зупинка розташована в місці, поданому зовнішнім словником Schema.org."),
}

DATA_PROPS = {
    "routeId": ("ідентифікатор маршруту", "TransportRoute", "xsd:string", "functional", "Унікальний ідентифікатор маршруту з GTFS routes.txt."),
    "routeType": ("тип маршруту", "TransportRoute", "xsd:integer", "functional", "Код виду транспорту GTFS: 3 — автобус, 0 — трамвай, 11 — тролейбус."),
    "stopId": ("ідентифікатор зупинки", "Stop", "xsd:string", "functional", "Унікальний ідентифікатор зупинки з GTFS stops.txt."),
    "stopName": ("назва зупинки", "Stop", "xsd:string", "functional", "Людиночитана назва зупинки."),
    "latitude": ("широта", "Stop", "xsd:decimal", "functional", "Географічна широта зупинки в градусах."),
    "longitude": ("довгота", "Stop", "xsd:decimal", "functional", "Географічна довгота зупинки в градусах."),
    "wheelchairAccessible": ("доступність", "Stop", "xsd:boolean", "functional", "Ознака доступності зупинки для маломобільних пасажирів."),
    "tripId": ("ідентифікатор рейсу", "Trip", "xsd:string", "functional", "Унікальний ідентифікатор рейсу з GTFS trips.txt."),
    "departureTime": ("час відправлення", "StopTime", "xsd:string", "functional", "Плановий час відправлення рейсу з зупинки."),
    "stopSequence": ("порядковий номер зупинки", "StopTime", "xsd:integer", "functional", "Номер зупинки в послідовності рейсу."),
    "headwayMinutes": ("інтервал, хв", "Frequency", "xsd:integer", "functional", "Проміжок між послідовними відправленнями рейсів у хвилинах."),
    "passengerCount": ("кількість пасажирів", "PassengerFlow", "xsd:integer", "functional", "Кількість валідованих пасажирів за інтервал спостереження."),
    "loadFactor": ("коефіцієнт завантаженості", "LoadFactor", "xsd:decimal", "functional", "Відношення кількості пасажирів до місткості транспортного засобу."),
    "delayMinutes": ("затримка, хв", "Delay", "xsd:integer", "functional", "Відхилення фактичного часу відправлення від планового в хвилинах."),
    "travelTimeMinutes": ("час у дорозі, хв", "TravelTime", "xsd:integer", "functional", "Тривалість проходження ділянки або рейсу в хвилинах."),
    "validFrom": ("дійсний від", "ServiceCalendar", "xsd:string", "functional", "Перша дата дії календаря обслуговування."),
    "validTo": ("дійсний до", "ServiceCalendar", "xsd:string", "functional", "Остання дата дії календаря обслуговування."),
    "agencyName": ("назва перевізника", "TransportAgency", "xsd:string", "functional", "Офіційна назва транспортного перевізника."),
    "personName": ("ім’я учасника", "Actor", "xsd:string", "functional", "Людиночитане ім’я пасажира, водія або диспетчера."),
    "sensorId": ("ідентифікатор сенсора", "Sensor", "xsd:string", "functional", "Унікальний ідентифікатор пристрою вимірювання."),
    "datasetName": ("назва набору даних", "DataAsset", "xsd:string", "functional", "Людиночитана назва джерела даних."),
    "vehicleId": ("ідентифікатор транспортного засобу", "Vehicle", "xsd:string", "functional", "Унікальний ідентифікатор рухомого складу."),
    "capacity": ("місткість", "Vehicle", "xsd:integer", "functional", "Максимальна кількість пасажирів транспортного засобу."),
    "eventTime": ("час події", "Event", "xsd:dateTime", "functional", "Дата й час виникнення події на мережі."),
    "confidence": ("впевненість прогнозу", "Forecast", "xsd:decimal", "functional", "Оцінка достовірності прогнозу від 0 до 1."),
}

INDIVIDUALS = {}

def ind(iri, types, props):
    INDIVIDUALS[iri] = (types, props)

ind("System_Lviv", ["TransportSystem"], [("hasPart", "Network_Lviv"), ("rdfs:label", "Транспортна система Львова")])
ind("Network_Lviv", ["TransportNetwork"], [("partOf", "System_Lviv")])
ind("Route_9", ["BusRoute"], [("routeId", "9"), ("routeType", 3), ("servesStop", ["Stop_Vokzal", "Stop_Rynok", "Stop_Politekhnika"]), ("hasTrip", ["Trip_9_0800", "Trip_9_0830"]), ("routeFrequency", "Frequency_R9")])
ind("Route_25", ["BusRoute"], [("routeId", "25"), ("routeType", 3), ("servesStop", ["Stop_Vokzal", "Stop_Universytet"]), ("hasTrip", ["Trip_25_0815"])])
ind("Route_31", ["TramRoute"], [("routeId", "31"), ("routeType", 0), ("servesStop", ["Stop_Vokzal", "Stop_Rynok"]), ("hasTrip", ["Trip_31_0700"])])
ind("Stop_Vokzal", ["Stop"], [("stopId", "S001"), ("stopName", "Вокзал"), ("latitude", 49.8397), ("longitude", 24.0045), ("wheelchairAccessible", True), ("servedByRoute", ["Route_9", "Route_25", "Route_31"])])
ind("Stop_Rynok", ["Stop"], [("stopId", "S002"), ("stopName", "Площа Ринок"), ("latitude", 49.8419), ("longitude", 24.0315), ("wheelchairAccessible", False), ("servedByRoute", ["Route_9", "Route_31"])])
ind("Stop_Politekhnika", ["Stop"], [("stopId", "S003"), ("stopName", "Політехніка"), ("latitude", 49.8355), ("longitude", 24.0120), ("wheelchairAccessible", True), ("servedByRoute", ["Route_9"])])
ind("Stop_Universytet", ["Stop"], [("stopId", "S004"), ("stopName", "Університет"), ("latitude", 49.8380), ("longitude", 24.0220), ("wheelchairAccessible", False), ("servedByRoute", ["Route_25"])])
ind("Seg_Vokzal_Rynok", ["NetworkSegment"], [("hasEvent", "Congestion_Horodotska"), ("rdfs:label", "Вокзал — Площа Ринок")])
ind("Seg_Rynok_Politekhnika", ["NetworkSegment"], [("hasEvent", "Roadwork_Stryiska"), ("rdfs:label", "Площа Ринок — Політехніка")])
ind("Trip_9_0800", ["Trip"], [("tripId", "T090800"), ("tripOfRoute", "Route_9"), ("startsAt", "Stop_Vokzal"), ("endsAt", "Stop_Rynok"), ("usesVehicle", "Bus_2501"), ("operatedBy", "Agency_LvivAvtobus"), ("hasDriver", "Driver_01"), ("hasState", "State_Delayed_9"), ("hasStopTime", ["StopTime_T9_Vokzal", "StopTime_T9_Rynok", "StopTime_T9_Politekhnika"]), ("hasMeasurement", ["Delay_9_0800", "Load_9_0800", "TravelTime_9_0800"]), ("affectedByEvent", "Congestion_Horodotska")])
ind("Trip_9_0830", ["Trip"], [("tripId", "T090830"), ("tripOfRoute", "Route_9"), ("startsAt", "Stop_Vokzal"), ("endsAt", "Stop_Rynok"), ("usesVehicle", "Bus_2502"), ("operatedBy", "Agency_LvivAvtobus"), ("hasState", "State_OnTime_9_0830")])
ind("Trip_25_0815", ["Trip"], [("tripId", "T250815"), ("tripOfRoute", "Route_25"), ("startsAt", "Stop_Vokzal"), ("endsAt", "Stop_Universytet"), ("usesVehicle", "Bus_2502"), ("operatedBy", "Agency_LvivAvtobus"), ("hasState", "State_OnTime_25")])
ind("Trip_31_0700", ["Trip"], [("tripId", "T310700"), ("tripOfRoute", "Route_31"), ("startsAt", "Stop_Vokzal"), ("endsAt", "Stop_Rynok"), ("usesVehicle", "Tram_0903"), ("operatedBy", "Agency_LvivElektrotrans"), ("hasDriver", "Driver_02"), ("hasState", "State_OnTime_31")])
ind("Bus_2501", ["Bus"], [("vehicleId", "B2501"), ("capacity", 90), ("assignedToTrip", "Trip_9_0800")])
ind("Bus_2502", ["Bus"], [("vehicleId", "B2502"), ("capacity", 85), ("assignedToTrip", ["Trip_9_0830", "Trip_25_0815"])])
ind("Tram_0903", ["Tram"], [("vehicleId", "T0903"), ("capacity", 180), ("assignedToTrip", "Trip_31_0700")])
ind("Trolleybus_1101", ["Trolleybus"], [("vehicleId", "TB1101"), ("capacity", 110)])
ind("Driver_01", ["Driver"], [("personName", "Іван Петренко"), ("drivesTrip", "Trip_9_0800")])
ind("Driver_02", ["Driver"], [("personName", "Олена Коваль"), ("drivesTrip", "Trip_31_0700")])
ind("Dispatcher_01", ["Dispatcher"], [("personName", "Марія Шевчук"), ("respondsTo", "Congestion_Horodotska")])
ind("Passenger_P01", ["Passenger"], [("personName", "Андрій Мельник"), ("passengerRecommendation", "Recommendation_R1")])
ind("Passenger_P02", ["Passenger"], [("personName", "Софія Бондар")])
ind("Agency_LvivAvtobus", ["TransportAgency"], [("agencyName", "ЛьвівАвтобус"), ("operatesTrip", ["Trip_9_0800", "Trip_9_0830", "Trip_25_0815"])])
ind("Agency_LvivElektrotrans", ["TransportAgency"], [("agencyName", "ЛьвівЕлектротранс"), ("operatesTrip", "Trip_31_0700")])
ind("GPS_2501", ["GPSTracker"], [("sensorId", "GPS-2501"), ("measures", ["Delay_9_0800", "TravelTime_9_0800"])])
ind("Validator_Vokzal", ["TicketValidator"], [("sensorId", "VAL-S001"), ("measures", "Flow_Vokzal_0800")])
ind("Counter_2501", ["PassengerCounter"], [("sensorId", "CNT-2501"), ("measures", "Load_9_0800")])
ind("Delay_9_0800", ["Delay"], [("delayMinutes", 12), ("measurementOf", "Trip_9_0800"), ("measuredBy", "GPS_2501")])
ind("Load_9_0800", ["LoadFactor"], [("loadFactor", 0.92), ("measurementOf", "Trip_9_0800"), ("measuredBy", "Counter_2501")])
ind("TravelTime_9_0800", ["TravelTime"], [("travelTimeMinutes", 38), ("measurementOf", "Trip_9_0800")])
ind("Flow_Vokzal_0800", ["PassengerFlow"], [("passengerCount", 120), ("measuredBy", "Validator_Vokzal")])
ind("Congestion_Horodotska", ["Congestion"], [("eventTime", "2026-10-27T08:10:00"), ("affectsSegment", "Seg_Vokzal_Rynok"), ("affectsTrip", "Trip_9_0800"), ("handledBy", "Dispatcher_01")])
ind("Roadwork_Stryiska", ["Roadwork"], [("eventTime", "2026-10-27T07:00:00"), ("affectsSegment", "Seg_Rynok_Politekhnika")])
ind("State_Delayed_9", ["DelayedState"], [("stateOfTrip", "Trip_9_0800")])
ind("State_OnTime_9_0830", ["OnTimeState"], [("stateOfTrip", "Trip_9_0830")])
ind("State_OnTime_25", ["OnTimeState"], [("stateOfTrip", "Trip_25_0815")])
ind("State_OnTime_31", ["OnTimeState"], [("stateOfTrip", "Trip_31_0700")])
ind("Calendar_2026", ["ServiceCalendar"], [("validFrom", "2026-01-01"), ("validTo", "2026-12-31"), ("rdfs:label", "Будні 2026")])
ind("StopTime_T9_Vokzal", ["StopTime"], [("departureTime", "08:00:00"), ("stopSequence", 1), ("atStop", "Stop_Vokzal"), ("stopTimeOfTrip", "Trip_9_0800")])
ind("StopTime_T9_Rynok", ["StopTime"], [("departureTime", "08:20:00"), ("stopSequence", 2), ("atStop", "Stop_Rynok"), ("stopTimeOfTrip", "Trip_9_0800")])
ind("StopTime_T9_Politekhnika", ["StopTime"], [("departureTime", "08:30:00"), ("stopSequence", 3), ("atStop", "Stop_Politekhnika"), ("stopTimeOfTrip", "Trip_9_0800")])
ind("StopTime_T31_Vokzal", ["StopTime"], [("departureTime", "07:00:00"), ("stopSequence", 1), ("atStop", "Stop_Vokzal"), ("stopTimeOfTrip", "Trip_31_0700")])
ind("Frequency_R9", ["Frequency"], [("headwayMinutes", 10), ("frequencyOfRoute", "Route_9")])
ind("Frequency_R25", ["Frequency"], [("headwayMinutes", 15), ("frequencyOfRoute", "Route_25")])
ind("GTFS_Lviv", ["GTFSDataset"], [("datasetName", "GTFS Lviv 2026"), ("datasetDescribes", "Network_Lviv")])
ind("SIRI_Lviv", ["SIRIFeed"], [("datasetName", "SIRI Lviv realtime"), ("datasetDescribes", "Network_Lviv")])
ind("NeTEx_Lviv", ["NeTExDataset"], [("datasetName", "NeTEx Lviv 2026"), ("datasetDescribes", "Network_Lviv")])
ind("Forecast_9_Peak", ["Forecast"], [("confidence", 0.87), ("forecastFor", "Trip_9_0800")])
ind("Decision_D1", ["DecisionSupport"], [("basedOnForecast", "Forecast_9_Peak"), ("hasRecommendation", "Recommendation_R1")])
ind("Recommendation_R1", ["Recommendation"], [("recommends", "Route_31"), ("forPassenger", "Passenger_P01"), ("recommendationOfDecision", "Decision_D1")])

SITUATIONS = [
    ["S1", "Затор у годину пік", "mm:OnTimeState", "mm:Congestion", "delayMinutes > 10 і loadFactor > 0,85", "mm:DelayedState", "Диспетчер додає резервний рейс; пасажиру рекомендується трамвай", "mm:Event", "mm:TransportState", "mm:DispatchDecision", "mm:GPSTracker", "1.0", "Невмержицький Максим", "GTFS Reference 2026; SIRI; ЛР6", "verified"],
    ["S2", "Поломка транспортного засобу", "mm:OnTimeState", "mm:VehicleFailure", "немає резервного ТЗ на маршруті", "mm:DelayedState", "Призначити резервний автобус і повідомити пасажирів", "mm:Event", "mm:TransportState", "mm:DispatchDecision", "mm:GPSTracker", "1.0", "Невмержицький Максим", "GTFS Reference 2026; SIRI", "verified"],
    ["S3", "Сплеск пасажиропотоку", "mm:OnTimeState", "mm:PassengerSurge", "passengerCount > 100 і loadFactor > 0,85", "mm:CrowdedState", "Подати додатковий рейс і рекомендувати пересадку", "mm:Event", "mm:TransportState", "mm:Recommendation", "mm:TicketValidator", "1.0", "Невмержицький Максим", "ЛР6; GTFS; SIRI", "verified"],
    ["S4", "Ремонт дороги", "mm:OnTimeState", "mm:Roadwork", "ділянка закрита або звужена", "mm:DelayedState", "Змінити маршрут і перерахувати час у дорозі", "mm:Event", "mm:TransportState", "mm:DispatchDecision", "mm:GPSTracker", "1.0", "Невмержицький Максим", "GTFS Reference 2026; ЛР6", "verified"],
    ["S5", "Погіршення погоди", "mm:OnTimeState", "mm:WeatherEvent", "швидкість руху нижча за 20 км/год", "mm:DelayedState", "Збільшити інтервал і попередити пасажирів", "mm:Event", "mm:TransportState", "mm:Recommendation", "mm:GPSTracker", "1.0", "Невмержицький Максим", "SIRI; ЛР6", "verified"],
]

CQS = [
    ["CQ1", "Які зупинки є пересадочними?", "cq01_interchange_stops.rq", 2, "Stop_Vokzal; Stop_Rynok"],
    ["CQ2", "Які маршрути обслуговують зупинку «Вокзал»?", "cq02_routes_at_vokzal.rq", 3, "Route_9; Route_25; Route_31"],
    ["CQ3", "Які рейси мають стан затримки?", "cq03_delayed_trips.rq", 1, "Trip_9_0800"],
    ["CQ4", "Яка ділянка і який рейс зазнали впливу затору?", "cq04_congestion_impact.rq", 1, "Seg_Vokzal_Rynok; Trip_9_0800"],
    ["CQ5", "Які зупинки доступні для маломобільних пасажирів?", "cq05_accessible_stops.rq", 2, "Stop_Vokzal; Stop_Politekhnika"],
    ["CQ6", "Які маршрути мають інтервал руху не більше 10 хвилин?", "cq06_frequent_routes.rq", 1, "Route_9"],
    ["CQ7", "Які рейси виконуються автобусами?", "cq07_bus_trips.rq", 3, "Trip_9_0800; Trip_9_0830; Trip_25_0815"],
    ["CQ8", "Яке рішення і рекомендацію підтримує прогноз?", "cq08_forecast_decision.rq", 1, "Decision_D1; Recommendation_R1; Route_31"],
    ["CQ9", "Які рейси мають затримку понад 10 хвилин?", "cq09_delay_over_10.rq", 1, "Trip_9_0800"],
    ["CQ10", "Які джерела даних описують транспортну мережу?", "cq10_datasets_for_network.rq", 3, "GTFS_Lviv; SIRI_Lviv; NeTEx_Lviv"],
]

CLAIMS = [
    ["C01", "Транспортна мережа складається із зупинок, ділянок і маршрутів.", "факт", "GTFS Reference 2026", "V2", "verified", "Підтверджено структурою GTFS."],
    ["C02", "Пересадочна зупинка обслуговується щонайменше двома маршрутами.", "правило", "ЛР6; моделювання", "V4", "verified", "Перевірено HermiT на Stop_Vokzal і Stop_Rynok."],
    ["C03", "Рейс виконується рівно одним транспортним засобом.", "правило", "GTFS trips.txt", "V4", "verified", "Кардинальність usesVehicle = 1."],
    ["C04", "Кожен рейс має рівно один перевізник.", "правило", "GTFS agency.txt", "V4", "verified", "Кардинальність operatedBy = 1."],
    ["C05", "Затримка є подією, а не вимірюванням.", "гіпотеза", "Чернетка LLM", "V1", "rejected", "Затримка — вимірювання; подією є затор або ремонт."],
    ["C06", "Пасажир є різновидом транспортного засобу.", "гіпотеза", "Чернетка LLM", "V1", "rejected", "Порушення OntoClean: різні категорії та ідентичність."],
    ["C07", "Маршрут має рівно одну зупинку.", "гіпотеза", "Чернетка LLM", "V1", "rejected", "Кардинальність хибна: маршрут обслуговує багато зупинок."],
    ["C08", "Зупинка «Вокзал» обслуговується трьома маршрутами.", "факт", "data/individuals.csv", "V3", "verified", "Route_9, Route_25, Route_31."],
    ["C09", "Затор на вул. Городоцькій впливає на рейс 9 о 08:00.", "факт", "data/individuals.csv", "V3", "verified", "affectedByEvent і hasEvent."],
    ["C10", "Рекомендація R1 пропонує трамвайний маршрут 31.", "факт", "data/individuals.csv", "V3", "verified", "recommends Route_31."],
    ["C11", "GTFS описує мережу, розклад і тарифи.", "факт", "GTFS Reference 2026", "V2", "verified", "Підтверджено розділами reference."],
    ["C12", "SIRI передає дані реального часу.", "факт", "SIRI; Transmodel", "V2", "verified", "Підтверджено призначенням стандарту."],
    ["C13", "Усі рейси міста мають затримку понад 10 хвилин.", "гіпотеза", "Чернетка LLM", "V1", "rejected", "Спростовується даними: лише Trip_9_0800."],
    ["C14", "Карта ЛР6 містить 106 пропозицій.", "факт", "ЛР6", "V3", "verified", "models/triples_final.csv."],
    ["C15", "Кожна зупинка доступна для маломобільних пасажирів.", "гіпотеза", "Чернетка LLM", "V1", "rejected", "Лише 2 з 4 зупинок мають wheelchairAccessible=true."],
    ["C16", "Онтологія відкривається в Protégé і парситься rdflib.", "факт", "Перевірка", "V4", "verified", "Парсинг успішний; файл OWL 2 Turtle."],
    ["C17", "Кількість класів у LLM-чернетці достатня для всіх CQ.", "гіпотеза", "Чернетка LLM", "V2", "rejected", "Частка проходження CQ нижча, ніж в експертній онтології."],
    ["C18", "HermiT виявив навмисну суперечність Bus/Tram.", "факт", "docs/reasoner_log.md", "V4", "verified", "InconsistentOntologyException."],
]

SOURCES = [
    ["GTFS Reference 2026", "https://gtfs.org/documentation/schedule/reference/", "2026-10-27"],
    ["Transmodel (Wikipedia, rev. 1277981919)", "https://en.wikipedia.org/wiki/Transmodel", "2026-10-27"],
    ["Intelligent transportation system (Wikipedia)", "https://en.wikipedia.org/wiki/Intelligent_transportation_system", "2026-10-27"],
    ["Schema.org", "https://schema.org/", "2026-10-27"],
    ["W3C OWL 2 Primer", "https://www.w3.org/TR/owl2-primer/", "2026-10-27"],
    ["Guarino & Welty, OntoClean", "https://doi.org/10.1145/505168.505170", "2026-10-27"],
]
