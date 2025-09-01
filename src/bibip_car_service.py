from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale
import os
import json
from collections import defaultdict


class CarService:
    def __init__(self, root_directory_path: str) -> None:
        self.root_directory_path = root_directory_path

# Создаем доп. методы: 
    #  Добавление строки в файл/возврат ее позиции 
    def _append_to_file(self, filename: str, data: str) -> int:
        filepath = os.path.join(self.root_directory_path, filename) #формирование пути к файлу
        with open(filepath, 'a') as f: # открытие в режиме 'a'
            position = f.tell()  # возвращение текущей позиции
            f.write(data + '\n') # запись в файл
        return position

    # Добавление в индек. файл запись в формате "ключ:позиция" для поиска по ключу
    def _update_index(self, filename: str, key: str, position: int) -> None:
        index_file = os.path.join(self.root_directory_path, filename)
        with open(index_file, 'a') as f: #формирование пути к файлу
            f.write(f"{key}:{position}\n") # запись в файл

    # Чтение индек. файла и преобразование его содержимого в словарь
    def _read_index_to_dict(self, index_filename: str) -> dict[str, int]:
        index_path = os.path.join(self.root_directory_path, index_filename)
        if not os.path.exists(index_path): # проверка, есть ли файл
            return {}
        index_dict = {}
        with open(index_path, 'r') as f: # открытие в режиме 'r'
            for line in f:
                parts = line.strip().split(':') # разбиваем стороку по ':'
                if len(parts) < 2: # проверка строки(если не полная: ключ, значение) 
                    continue
                key = parts[0]
                offset = int(parts[1]) # преобразование 2-й части в число
                index_dict[key] = offset #добавление в словарь
        return index_dict

    # Записываем содержимое словаря в файл
    def _write_index(self, index_filename: str, index_dict: dict[str, int]) -> None:
        index_path = os.path.join(self.root_directory_path, index_filename)
        with open(index_path, 'w') as f:
            for key, offset in index_dict.items():
                f.write(f"{key}:{offset}\n")

    # Читаем все модели из файла 'models.txt'(возвращаем словарь)
    def _read_all_models(self) -> dict[int, Model]: 
        models_path = os.path.join(self.root_directory_path, 'models.txt')
        models = {}
        if not os.path.exists(models_path): # проверка, есть ли файл
            return models
        with open(models_path, 'r') as f: 
            for line in f:
                try:
                    model_data = json.loads(line.strip()) # разбиваем стороку по пробелу и преобразуем в словарь
                    model = Model(**model_data) #создаем объект и в него распаковываем словарь(как аргумент)
                    models[model.id] = model # добавляем созданный объект в словарь по ключю ID
                except json.JSONDecodeError: #обрабатываем исключение, если не смогли обрабоать строку
                    continue
        return models
    
    # Аналогичен _read_all_models, но работает с автомобилями.
    def _read_all_cars(self) -> dict[str, Car]: 
        cars_path = os.path.join(self.root_directory_path, 'cars.txt') 
        cars = {} 
        if not os.path.exists(cars_path):
            return cars
        with open(cars_path, 'r') as f: 
            for line in f: #
                try:
                    car_data = json.loads(line.strip())
                    car = Car(**car_data) 
                    cars[car.vin] = car
                except json.JSONDecodeError:
                    continue
        return cars

     # Задание 1. Сохранение автомобилей и моделей
    def add_model(self, model: Model) -> Model:
        model_data = model.model_dump_json()
        position = self._append_to_file('models.txt', model_data)
        self._update_index('models_index.txt', str(model.id), position)
        return model

     # Задание 1. Сохранение автомобилей и моделей
    def add_car(self, car: Car) -> Car:
        car_data = car.model_dump_json()
        position = self._append_to_file('cars.txt', car_data)
        self._update_index('cars_index.txt', car.vin, position)
        return car
    
    # Задание 2. Сохранение продаж.
    def sell_car(self, sale: Sale) -> Car:
        cars_file = os.path.join(self.root_directory_path, "cars.txt")
        cars_index = self._read_index_to_dict('cars_index.txt')
        
        if sale.car_vin not in cars_index:
            raise ValueError(f"Car with VIN {sale.car_vin} not found")
        
        with open(cars_file, 'r+') as f:
            f.seek(cars_index[sale.car_vin])
            car_data = json.loads(f.readline().strip())
            car = Car(**car_data)
            
            if car.status == CarStatus.sold:
                raise ValueError(f"Car with VIN {sale.car_vin} is already sold")
            
            car.status = CarStatus.sold
            updated_car_data = car.model_dump_json()
            
            f.seek(cars_index[sale.car_vin])
            f.write(updated_car_data + '\n')
        
        with open(os.path.join(self.root_directory_path, "sales.txt"), 'a') as f:
            sale_offset = f.tell()
            f.write(sale.model_dump_json() + '\n')
        
        sales_index = self._read_index_to_dict('sales_index.txt')
        sales_index[sale.car_vin] = sale_offset
        self._write_index('sales_index.txt', sales_index)
        
        return car
    # Задание 3. Доступные к продаже
    def get_cars(self, status: CarStatus) -> list[Car]:
        cars = []
        cars_path = os.path.join(self.root_directory_path, 'cars.txt')
        if not os.path.exists(cars_path):
            return cars
        with open(cars_path, 'r') as f:
            for line in f:
                try:
                    car_data = json.loads(line.strip())
                    car = Car(**car_data)
                    if car.status == status:
                        cars.append(car)
                except json.JSONDecodeError:
                    continue
        return cars
    
    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        cars_index = self._read_index_to_dict('cars_index.txt')
        if vin not in cars_index:
            return None

        cars_path = os.path.join(self.root_directory_path, 'cars.txt')
        with open(cars_path, 'r') as f:
            f.seek(cars_index[vin])
            car_data = json.loads(f.readline().strip())
            car = Car(**car_data)

        models_index = self._read_index_to_dict('models_index.txt')
        model_id_str = str(car.model)
        if model_id_str not in models_index:
            return None

        models_path = os.path.join(self.root_directory_path, 'models.txt')
        with open(models_path, 'r') as f:
            f.seek(models_index[model_id_str])
            model_data = json.loads(f.readline().strip())
            model = Model(**model_data)

        sales_index = self._read_index_to_dict('sales_index.txt')
        sales_path = os.path.join(self.root_directory_path, 'sales.txt')
        if vin in sales_index:
            with open(sales_path, 'r') as f:
                f.seek(sales_index[vin])
                sale_data = json.loads(f.readline().strip())
                sale = Sale(**sale_data)
            sales_date = sale.sales_date
            sales_cost = sale.cost
        else:
            sales_date = None
            sales_cost = None

        return CarFullInfo(
            vin=car.vin,
            car_model_name=model.name,
            car_model_brand=model.brand,
            price=car.price,
            date_start=car.date_start,
            status=car.status,
            sales_date=sales_date,
            sales_cost=sales_cost
        )
    # Задание 5. Обновление ключевого поля
    def update_vin(self, vin: str, new_vin: str) -> Car:
        cars_index = self._read_index_to_dict('cars_index.txt')
        if new_vin in cars_index:
            raise ValueError(f"Car with VIN {new_vin} already exists")
        if vin not in cars_index:
            raise ValueError(f"Car with VIN {vin} not found")

        cars_path = os.path.join(self.root_directory_path, 'cars.txt')
        with open(cars_path, 'r+') as f:
            f.seek(cars_index[vin])
            car_data = json.loads(f.readline().strip())
            car = Car(**car_data)
            car.vin = new_vin
            updated_car_data = car.model_dump_json()
            f.seek(cars_index[vin])
            f.write(updated_car_data + '\n')

        cars_index[new_vin] = cars_index.pop(vin)
        self._write_index('cars_index.txt', cars_index)

        sales_index = self._read_index_to_dict('sales_index.txt')
        if vin in sales_index:
            sales_path = os.path.join(self.root_directory_path, 'sales.txt')
            with open(sales_path, 'r+') as f:
                f.seek(sales_index[vin])
                sale_data = json.loads(f.readline().strip())
                sale = Sale(**sale_data)
                sale.car_vin = new_vin
                updated_sale_data = sale.model_dump_json()
                f.seek(sales_index[vin])
                f.write(updated_sale_data + '\n')

            sales_index[new_vin] = sales_index.pop(vin)
            self._write_index('sales_index.txt', sales_index)
        return car
    
    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str) -> Car:
        sales_path = os.path.join(self.root_directory_path, 'sales.txt')
        found = None
        with open(sales_path, 'r') as f:
            pos = f.tell()
            line = f.readline()
            while line:
                try:
                    sale_data = json.loads(line.strip())
                    sale = Sale(**sale_data)
                    if sale.sales_number == sales_number:
                        found = (sale, pos)
                        break
                except json.JSONDecodeError:
                    pass
                pos = f.tell()
                line = f.readline()

        if found is None:
            raise ValueError(f"Sale with sales number {sales_number} not found")

        sale, sale_offset = found
        vin = sale.car_vin

        sales_index = self._read_index_to_dict('sales_index.txt')
        if vin in sales_index and sales_index[vin] == sale_offset:
            del sales_index[vin]
            self._write_index('sales_index.txt', sales_index)

        cars_index = self._read_index_to_dict('cars_index.txt')
        if vin not in cars_index:
            raise ValueError(f"Car with VIN {vin} not found")

        cars_path = os.path.join(self.root_directory_path, 'cars.txt')
        with open(cars_path, 'r+') as f:
            f.seek(cars_index[vin])
            car_data = json.loads(f.readline().strip())
            car = Car(**car_data)
            car.status = CarStatus.available
            updated_car_data = car.model_dump_json()
            f.seek(cars_index[vin])
            f.write(updated_car_data + '\n')
        return car
    
    # Задание 7. Самые продаваемые модели
    def top_models_by_sales(self) -> list[ModelSaleStats]:
        sales_index = self._read_index_to_dict('sales_index.txt')
        cars_dict = self._read_all_cars()
        models_dict = self._read_all_models()

        model_count = defaultdict(int)
        sales_path = os.path.join(self.root_directory_path, 'sales.txt')
        for vin, offset in sales_index.items():
            with open(sales_path, 'r') as f:
                f.seek(offset)
                try:
                    sale_data = json.loads(f.readline().strip())
                    sale = Sale(**sale_data)
                except json.JSONDecodeError:
                    continue
            if vin not in cars_dict:
                continue
            car = cars_dict[vin]
            if car.model not in models_dict:
                continue
            model = models_dict[car.model]
            model_count[(model.name, model.brand)] += 1

        result = []
        for (name, brand), count in model_count.items():
            result.append(ModelSaleStats(
                car_model_name=name,
                brand=brand,
                sales_number=count
            ))

        result.sort(key=lambda x: x.sales_number, reverse=True)
        return result[:3]
