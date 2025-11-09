# 📚 Теорія: Конструктивна Твердотільна Геометрія (CSG)

## 1. Концепція CSG

Конструктивна Твердотільна Геометрія (Constructive Solid Geometry, CSG) — це техніка моделювання, яка дозволяє створювати складні геометричні форми шляхом поєднання простіших фігур (примітивів) за допомогою булевих операцій.

**Ключові компоненти:**

1.  **Примітиви (Primitives):** Базові форми (наприклад, `RectangularSection`, коло). Вони є **листами** у CSG-дереві.
2.  **Операції (Operations):** Булеві функції, що визначають, як примітиви комбінуються. Вони є **вузлами** у CSG-дереві.

### 1.1. CSG-дерево
Результат кожної булевої операції є новим об'єктом, який сам може бути операндом для наступної операції. Таким чином, складна форма представляється як **бінарне дерево** (CSG-дерево), де листи — це примітиви, а вузли — булеві операції (`UNION`, `DIFFERENCE`, `INTERSECTION`).

## 2. Реалізація CSG за допомогою Shapely

У 2D-системах, таких як Geometrix, CSG-операції ефективно реалізуються за допомогою бібліотеки **Shapely** (яка є інтерфейсом до високопродуктивної бібліотеки GEOS).

* **Примітиви:** Кожен примітив має метод, який повертає його представлення у форматі **Shapely** (`shapely_geometry`).
* **Операції:** Класи `UnionOperation`, `DifferenceOperation` та `IntersectionOperation` просто викликають відповідні методи Shapely (`.union()`, `.difference()`, `.intersection()`).

Це гарантує **точне та надійне** обчислення результуючого контуру, що є критично важливим для наступного етапу — розрахунку властивостей.

## 3. Обчислення Інерційних Властивостей

Після виконання булевої операції (наприклад, $A - B$), нам потрібні точні геометричні суми ($A_{final}, S_{x, final}, I_{x, final}, \dots$). Через складність результуючої форми (з отворами, багатокутні контури), використання простих правил додавання/віднімання сум (*наприклад, $S_{x, A-B} = S_{x, A} - S_{x, B}$*) є **неточним** і може призвести до помилок через подвійне врахування областей перекриття.

### 3.1. Розрахунок за Контуром (Robust Summation)
Для забезпечення точності Geometrix використовує метод, який базується на інтегруванні по контуру фінальної Shapely геометрії (функція `_calculate_sums_from_shapely`):

1.  **Нормалізація:** Фінальна форма Shapely (Polygon або MultiPolygon) розкладається на окремі багатокутники.
2.  **Інтегрування:** Для кожного багатокутника використовується формула, що базується на координатах вершин (формула площі Гауса), для обчислення сирих геометричних сум.
3.  **Отвори:** Контури отворів (interior rings) інтегруються у **зворотному напрямку**, що автоматично призводить до **віднімання** їхніх геометричних сум від суми зовнішнього контуру.

Цей метод гарантує, що агреговані суми **($S_x, I_y, \dots$)** є точними, незалежно від складності булевої операції.

### 3.2. Центроїд та Центральні Моменти
Обчислення центроїда та центральних моментів інерції завжди відбувається уніфіковано:

1.  **Центроїд:** $c_x = S_y / A$, $c_y = S_x / A$.
2.  **Центральні Моменти:** Для перенесення моментів інерції відносно глобального початку $I_{x0}$ до центроїда $I_c$ використовується **Зворотна Теорема Штайнера (Reverse Steiner's Theorem):**
    $$I_c = I_{x0} - A \cdot c_y^2$$
Це завершує процес, забезпечуючи точний набір інерційних властивостей для будь-якої складної форми, отриманої за допомогою CSG.

***

# 📚 Theory: Constructive Solid Geometry (CSG)

## 1. The CSG Concept

Constructive Solid Geometry (CSG) is a modeling technique that allows complex geometric shapes to be built by combining simpler figures (primitives) using boolean operations.

**Key Components:**

1.  **Primitives:** Basic shapes (e.g., `RectangularSection`, circle). These are the **leaf nodes** in the CSG tree.
2.  **Operations:** Boolean functions that define how primitives are combined. These are the **nodes** in the CSG tree.

### 1.1. The CSG Tree
The result of every boolean operation is a new object which can itself be an operand for the next operation. Thus, a complex shape is represented as a **binary tree** (the CSG tree), where the leaves are primitives and the nodes are boolean operations (`UNION`, `DIFFERENCE`, `INTERSECTION`).

## 2. CSG Implementation with Shapely

In 2D systems, such as Geometrix, CSG operations are efficiently implemented using the **Shapely** library (an interface to the high-performance GEOS library).

* **Primitives:** Each primitive has a method that returns its **Shapely representation** (`shapely_geometry`).
* **Operations:** The `UnionOperation`, `DifferenceOperation`, and `IntersectionOperation` classes simply call the corresponding Shapely methods (`.union()`, `.difference()`, `.intersection()`).

This approach guarantees the **accurate and robust** calculation of the resulting contour, which is crucial for the next stage: property calculation.

## 3. Inertial Property Calculation

After a boolean operation (e.g., $A - B$), we need accurate geometric sums ($A_{final}, S_{x, final}, I_{x, final}, \dots$). Due to the complexity of the resulting shape (with holes, multi-part contours), using simple additive/subtractive rules for the sums (*e.g., $S_{x, A-B} = S_{x, A} - S_{x, B}$*) is **inaccurate** and can lead to errors due to double-counting of overlapping areas.

### 3.1. Contour-Based Calculation (Robust Summation)
To ensure accuracy, Geometrix uses a method based on integrating over the contour of the final Shapely geometry (the `_calculate_sums_from_shapely` function):

1.  **Normalization:** The final Shapely shape (Polygon or MultiPolygon) is broken down into individual `Polygon` objects.
2.  **Integration:** For each polygon, a vertex-based formula (like the Shoelace/Gauss area formula extension) is used to calculate the raw geometric sums.
3.  **Holes Handling:** The contours of internal holes (interior rings) are integrated in the **reverse direction**, which automatically results in the **subtraction** of their geometric sums from the exterior contour's sum.

This method guarantees that the aggregate sums **($S_x, I_y, \dots$)** are accurate, regardless of the complexity of the boolean operation.

### 3.2. Centroid and Central Moments
The calculation of the centroid and central moments of inertia is always performed in a unified way:

1.  **Centroid:** $c_x = S_y / A$, $c_y = S_x / A$.
2.  **Central Moments:** To transfer moments of inertia from the global origin $I_{x0}$ to the centroid $I_c$, the **Reverse Steiner's Theorem** is used:
    $$I_c = I_{x0} - A \cdot c_y^2$$
This completes the process, providing an accurate set of inertial properties for any complex shape derived through CSG.