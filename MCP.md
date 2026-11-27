# Easy Conifer: управление через Blender MCP

Инструкция для ИИ-агента, который управляет аддоном **Easy Conifer** (деревья и кусты на Geometry Nodes,
Blender 5+) через MCP-сервер Blender. Нужен инструмент выполнения Python внутри Blender
(`execute_blender_code` или аналог), желательно ещё `get_scene_info` и `get_viewport_screenshot`.

## 1. Главное правило

Не нажимай кнопки панели и не вызывай `bpy.ops.object.easy_conifer_*`: операторы зависят от выделения
и настроек сцены. Управляй **только через модуль API**:

```python
import bpy, json
ec = bpy.app.driver_namespace["easy_conifer_api"]   # модуль API, его публикует аддон
print(ec.help())                                    # список функций с сигнатурами
```

Пиши эти две строки в начале **каждого** вызова MCP: пространство имён между вызовами может не сохраняться.
`import easy_conifer_api` не используй: расширениям Blender запрещено регистрировать свои модули
верхнего уровня.

Если ключа `easy_conifer_api` нет, значит аддон выключен или его версия старше 0.9.0. Включи аддон:
`bpy.ops.preferences.addon_enable(module="bl_ext.user_default.easy_conifer")`. Если не получилось,
попроси пользователя.

Все функции работают без мыши и без 3D-вида, кроме `frame()`. Они возвращают dict, list или str.
Печатай результат так: `print(json.dumps(x, ensure_ascii=False, default=str))`.
При ошибке функция выбрасывает `ValueError` с понятным текстом: неизвестный пресет, параметр или имя
объекта, форма для не-куста. Прочитай текст и исправь вызов.

Один вызов MCP — один логический шаг. После каждого шага читай вывод.

## 2. Единицы и соглашения

- Метры, ось **+Z вверх**, +X — восток, +Y — север. Углы в градусах, поворот вокруг Z против часовой.
- Объекты адресуются **по имени** (`name` из результата `add`). Аргумент `names` принимает одно имя,
  список имён или `None`: тогда действие относится ко всем объектам Easy Conifer в сцене.
- Параметры задаются **по названию из интерфейса модификатора**: `"Height"`, `"Card Size"`,
  `"Surface Density"`. Полный список по типу — `ec.parameter_names("HEDGE")`, текущие значения объекта —
  `ec.parameters(name)`. Цвет передаётся как `[r, g, b, a]` в линейном пространстве, материал — по имени.
- Типы генераторов: `CONIFER` (ели, пихта), `BROADLEAF` (лиственные и свободные кусты), `HEDGE`
  (стриженые кусты). В `presets_list()` свободные кусты помечены `SHRUB`, а сделаны генератором `BROADLEAF`.
- Пресет нельзя применить к объекту другого типа: ель не станет берёзой. Такой объект попадёт
  в `skipped_other_kind`. Чтобы сменить тип, удали объект и создай новый.

## 3. Порядок работы

1. **Осмотреться:** `ec.version()`, `ec.scene_info()`.
2. **Выбрать пресет:** `ec.presets_list()` или `ec.presets_list("HEDGE")`; для стриженых — `ec.forms()`.
3. **Посадить:**
   - одно дерево — `ec.add(preset, (x, y, z), seed=…, params={…})`;
   - аллея или ряд отдельных кустов — `ec.add_row(preset, start, end, spacing)`;
   - группа по точкам — `ec.add_many(preset, points, rotation="random", scale_jitter=0.1)`;
   - сплошная стриженая изгородь — `ec.add_hedge(preset, start, end, height, depth, form="CUBE")`.
     Это **один** объект, вытянутый вдоль линии. Не собирай изгородь из десятков кубов.
4. **Настроить:** `ec.set_params(name, **{"Card Size": 0.3})`, `ec.apply_form(name, "TRAPEZOID",
   keep_size=True)`, `ec.new_seed(name)`.
5. **Проверить:** `ec.info(name)` — треугольники и предупреждения нод (`warnings` должен быть пуст);
   `ec.scene_info(with_tris=True)` — суммарный полигонаж.
6. **Показать:** `ec.frame(name)`, затем `get_viewport_screenshot`. Для рендера: Cycles,
   *Transparent Max Bounces* ≥ 32 (`add` поднимает его сам).
7. **Для экспорта:** `ec.realize(names)` превращает объекты в обычные меши с UV на атлас. Это
   необратимо, поэтому выполняй только по просьбе пользователя.

Полигонаж-ориентиры: стриженый куст 1,5–4 тыс. треугольников, ель 14 м ~40 тыс., берёза ~33 тыс.,
ива плакучая ~140 тыс. Для массовой посадки в генплане сначала посчитай сумму через
`scene_info(with_tris=True)`; при необходимости уменьши плотность (*Twig Density*, *Surface Density*).
Можно скрыть листву во вьюпорте: `ec.foliage_visible(False)`. На рендер это не влияет.

## 4. Справочник API

| Функция | Что делает |
|---|---|
| `help()` | список функций |
| `version()` | версии аддона, API и Blender |
| `presets_list(kind=None)` | пресеты `[{key, name, description, kind, section}]`; `kind`: CONIFER / BROADLEAF / SHRUB / HEDGE |
| `forms()` | формы стриженых кустов: BALL, CUBE, TRAPEZOID, NATURAL |
| `parameter_names(kind)` | параметры генератора по панелям: имя, тип, умолчание, min/max, описание |
| `parameters(name)` | текущие значения всех параметров объекта |
| `info(name)` | пресет, тип, сид, положение, поворот, треугольники, предупреждения нод |
| `scene_info(with_tris=False)` | все объекты Easy Conifer в сцене (+ треугольники при `with_tris=True`) |
| `add(preset, location=(0,0,0), seed=None, form=None, name=None, rotation=0, params=None, collection=None)` | посадить дерево или куст; `seed=None` — случайный; `form` только для HEDGE_*; `collection` создаётся при отсутствии |
| `add_many(preset, points, seed=None, form=None, params=None, rotation="random", scale_jitter=0, collection=None)` | по объекту на точку; сиды seed, seed+1, … |
| `add_row(preset, start, end, spacing, seed=None, form=None, params=None, rotation="along", collection=None)` | ряд от start до end с шагом spacing (включая оба конца) |
| `add_hedge(preset, start, end, height=1.0, depth=0.8, form="CUBE", seed=None, params=None, name=None)` | сплошная изгородь одним объектом вдоль отрезка |
| `set_params(names, **values)` | задать параметры по имени из интерфейса |
| `apply_preset(names, preset, keep_seed=True)` | применить пресет к объектам того же типа; кусты сохраняют форму и размер |
| `apply_form(names, form, keep_size=False)` | сменить форму стриженых кустов |
| `new_seed(names, seed=None)` | новый сид (число или случайный), возвращает `{name: seed}` |
| `foliage_visible(show=True, names=None)` | листва/хвоя во вьюпорте |
| `delete(names)` | удалить объекты |
| `realize(names)` | применить модификатор → обычный меш для экспорта; `{name: треугольники}` |
| `rebuild()` | пересоздать группы нод из аддона (после обновления аддона) |
| `bake(species="ALL", resolution=2048, seed=0, density=1.0)` | перепечь атласы веточек; ~1–2 мин на вид при 2048, Blender блокируется |
| `bake_species()` | ключи видов для `bake` |
| `reset_textures()` | вернуть поставочные атласы |
| `frame(names=None, camera_view=False)` | навести 3D-вид на объекты (нужен интерфейс) |
| `tri_count(obj)` | треугольники объекта (принимает `bpy.types.Object`) |

## 5. Примеры

Двор: аллея лип, живая изгородь вдоль проезда, кусты-шары у входа.

```python
import bpy, json
ec = bpy.app.driver_namespace["easy_conifer_api"]
out = {
  "alley": ec.add_row("TILIA_CORDATA", (0, 0), (60, 0), spacing=8, seed=10, collection="Озеленение"),
  "hedge": ec.add_hedge("HEDGE_COTONEASTER", (0, -4), (60, -4), height=0.9, depth=0.7, seed=3),
  "balls": ec.add_many("HEDGE_PHYSO_DIABOLO", [(-3, 3), (-3, -3)], form="BALL", seed=5,
                       params={"Width": 1.0, "Depth": 1.0, "Height": 1.0}, collection="Озеленение"),
}
out["scene"] = ec.scene_info(with_tris=True)
print(json.dumps(out, ensure_ascii=False, default=str))
```

Перекрасить ели в голубой и сделать их ниже:

```python
import bpy, json
ec = bpy.app.driver_namespace["easy_conifer_api"]
spruces = [o["name"] for o in ec.scene_info()["objects"] if o["kind"] == "CONIFER"]
print(json.dumps(ec.set_params(spruces, Height=9, **{"Needle Color": [0.09, 0.17, 0.2, 1]}),
                 ensure_ascii=False))
```

## 6. Ограничения

- `bake()` и расчёт большого числа деревьев идут в главном потоке Blender, интерфейс на это время
  замирает. Пеки по одному виду за вызов MCP.
- `frame()` в фоновом режиме (`-b`) ничего не делает и возвращает `note`.
- Имена объектов Blender уникальны: вторая «Ель обыкновенная» получит суффикс `.001`. Бери имя из
  результата функции, а не угадывай его.
