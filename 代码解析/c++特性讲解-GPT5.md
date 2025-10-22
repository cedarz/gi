> 作者：莲子粥
链接：https://www.zhihu.com/question/451327108/answer/3299498791
来源：知乎
著作权归作者所有。商业转载请联系作者获得授权，非商业转载请注明出处。
>
> 肯定问模板，模板特化，SFINAE，type_traits，形参包，结构化绑定及其手搓，具名要求，迭代器trait，值类别，左右值、泛左值(glvalue)、纯右值(prvalue)，移动语义，转发引用(俗称万能引用)，std::forward<T>()完美转发，RAII，表达式求值，弃值表达式，不求值表达式，潜在求值表达式，常量表达式，临时量实质化(C++17)，标准布局类，用元编程实现constexpr编译期算法(如编译期汉诺塔，编译期递归，拼接字符数组，打函数表)，用户定义字面量，PIMPL，三五零原则，构造函数异常处理，函数 try 块，模块，全局模块片段及其存在的意义，模块分区，在CMake工程中声明模块范围库(范围适配器，定制点对象(CPO)，niebloid，ADL实参依赖查找，常见的范围工厂，视图，老式迭代器对和新式迭代器+哨位概念的对比)，可变仿引用对象的 operator= 成员必须带 const 限定的依据，奇特重现模板模式(CRTP)以及其在C++20范围适配器中的应用概念库，requires子句，约束的归入(subsume)，约束的偏序，concept，原子约束，约束规范化过程，范围库中常用的concept(可间接写入，可间接读取)协程，协程promise_type，挂起点，等待体，范围生成器，协程抛异常，格式化器特化，基本格式化器，格式串格式，显式对象形参(C++23)
>
>我在准备c++的面试，对于这里提到的每一项技术和特性，请给出其具体的c++标准版本（比如c++11），并给出比较详细的特性讲解，帮助我提高c++知识水平和面试技能，同时给出该特性的演示代码，供我学习。要求把这些内容，按序列号，输出为markdown格式，以便我后续导出整理。对于其他这里没有提及，而你认为对于c++从业者或者面试者比较重要的特性和技术点，也请一并罗列讲解并整理。


下面按序号整理你给出的每一个知识点，逐项标明引入或显著完善的标准版本，给出要点说明与简短可编译示例（示例代码的标准要求会在代码块首行用注释注明）。最后附上对面试很有帮助但题干里未列出的若干重要特性与示例。说明中若涉及多个版本演进，我会一并标注。

注：列表中的“肯定问模板”疑似输入法误写。结合上下文，我将其按“函数模板”处理；如与预期不符，请告知我调整。

---

## 1. 函数模板（疑似“肯定问模板”）
- 标准版本：C++98 起
- 要点：
  - 支持对函数进行模板化，根据实参类型进行模板参数推导与重载决议。
  - 与普通函数重载共同参与重载决议；函数模板不可做“偏特化”，只能用重载替代。
- 示例：
```cpp
// g++ -std=c++17 demo.cpp
#include <iostream>
template <class T>
T my_max(T a, T b) { return a < b ? b : a; }

// 重载：为字符串指针提供专门比较
const char* my_max(const char* a, const char* b) {
    return std::strcmp(a, b) < 0 ? b : a;
}

int main() {
    std::cout << my_max(3, 7) << "\n";          // 7
    std::cout << my_max(3.5, 2.1) << "\n";      // 3.5
    std::cout << my_max("ab", "aa") << "\n";    // ab
}
```

---

## 2. 模板特化（全特化与偏特化）
- 标准版本：C++98 起
- 要点：
  - 类模板支持“全特化”和“偏特化”；函数模板不支持偏特化（改用重载）。
  - 常用于根据类型类别定制行为。
- 示例：
```cpp
// g++ -std=c++17 demo.cpp
#include <type_traits>
#include <iostream>

template <class T> struct type_name { static constexpr const char* value = "unknown"; };
template <> struct type_name<int>    { static constexpr const char* value = "int"; };
template <class T> struct type_name<T*> { static constexpr const char* value = "pointer"; };

int main() {
    std::cout << type_name<int>::value << "\n";        // int（全特化）
    std::cout << type_name<double*>::value << "\n";    // pointer（偏特化）
    std::cout << type_name<float>::value << "\n";      // unknown
}
```

---

## 3. SFINAE（Substitution Failure Is Not An Error）
- 标准版本：C++98 规则确立；C++11 后常与 enable_if/type_traits 配合
- 要点：
  - 模板实参替换失败不报错，转为移除该重载候选。
  - 用于有条件参与重载、选择不同实现（检测惯用法/detection idiom）。
- 示例（检测是否存在 size() 成员）：
```cpp
// g++ -std=c++17 demo.cpp
#include <type_traits>
#include <iostream>
#include <vector>

template <class T>
auto has_size_impl(int) -> decltype(std::declval<const T&>().size(), std::true_type{});

template <class>
auto has_size_impl(...) -> std::false_type;

template <class T>
constexpr bool has_size_v = decltype(has_size_impl<T>(0))::value;

template <class T, std::enable_if_t<has_size_v<T>, int> = 0>
void print_size(const T& t) { std::cout << "size=" << t.size() << "\n"; }

template <class T, std::enable_if_t<!has_size_v<T>, int> = 0>
void print_size(const T&) { std::cout << "no size()\n"; }

int main() {
    std::vector<int> v{1,2,3};
    print_size(v);    // size=3
    print_size(42);   // no size()
}
```

---

## 4. <type_traits> 类型萃取
- 标准版本：C++11 引入，后续持续扩展（C++17/20/23）
- 要点：
  - 提供编译期类型信息与变换：is_integral、remove_reference、decay、conditional、invoke_result 等。
  - 常与 if constexpr / SFINAE / concepts 结合。
- 示例：
```cpp
// g++ -std=c++17 demo.cpp
#include <type_traits>
#include <iostream>

template <class T>
void f(T&& x) {
    using U = std::decay_t<T>;
    if constexpr (std::is_integral_v<U>) {
        std::cout << "integral: " << x << "\n";
    } else {
        std::cout << "not integral\n";
    }
}

int main() {
    f(42);          // integral
    f(3.14);        // not integral
    int a = 5; f(a);
}
```

---

## 5. 形参包（可变参数模板）与折叠表达式
- 标准版本：C++11（参数包），C++17（折叠表达式）
- 要点：
  - template<typename... Ts>；在函数、类模板中处理可变数量类型/实参。
  - 折叠表达式简化了递归展开。
- 示例：
```cpp
// g++ -std=c++17 demo.cpp
#include <iostream>

template <class... Args>
void print_csv(const Args&... args) {
    ((std::cout << args << (std::is_same_v<Args, typename std::tuple_element<sizeof...(Args)-1, std::tuple<Args...>>::type> ? "" : ",")), ...);
    std::cout << "\n";
}

// 更常见写法：简单输出并用逗号分隔
template <class... Args>
void print_line(const Args&... args) {
    // 左折叠，插入分隔符
    bool first = true;
    ((std::cout << (first ? (first=false, "") : ",") << args), ...);
    std::cout << "\n";
}

int main() {
    print_line(1, "a", 3.14);
}
```

---

## 6. 结构化绑定及其“手搓”（tuple-like 协议）
- 标准版本：C++17
- 要点：
  - auto [x, y] = obj; 需要对象满足 tuple-like 协议（tuple_size/tuple_element/get）。
  - “手搓”即自定义类型适配上述协议，使其可结构化绑定。
- 示例：
```cpp
// g++ -std=c++17 demo.cpp
#include <tuple>
#include <iostream>

struct Point { int x, y; };

// 为结构化绑定适配 tuple-like
namespace std {
template<> struct tuple_size<Point> : std::integral_constant<size_t, 2> {};
template<size_t I> struct tuple_element<I, Point> { using type = int; };
}

template <size_t I>
int& get(Point& p) {
    static_assert(I < 2);
    if constexpr (I == 0) return p.x; else return p.y;
}
template <size_t I>
const int& get(const Point& p) {
    static_assert(I < 2);
    if constexpr (I == 0) return p.x; else return p.y;
}

int main() {
    Point p{1,2};
    auto [a,b] = p;       // 结构化绑定
    std::cout << a << "," << b << "\n";
}
```

---

## 7. 具名要求（Named Requirements）
- 标准版本：C++98 起（在标准文本/附录中定义，C++20 由 concepts 形式化）
- 要点：
  - 如 “Swappable”、“MoveConstructible”、“RandomAccessIterator”等。
  - 在 C++20 之前是文字性描述；C++20 以 concepts/约束形式可被编译器检查。
- 示例（Swappable 的习惯性写法）： 
```cpp
// g++ -std=c++17 demo.cpp
#include <utility>
#include <iostream>

struct X {
    int v;
    friend void swap(X& a, X& b) noexcept {
        std::swap(a.v, b.v);
    }
};

int main() {
    X a{1}, b{2};
    using std::swap; // 允许 ADL 找到自定义 swap
    swap(a, b);
    std::cout << a.v << "," << b.v << "\n"; // 2,1
}
```

---

## 8. 迭代器 traits（std::iterator_traits）
- 标准版本：C++98 起
- 要点：
  - 为迭代器统一暴露 value_type、difference_type、iterator_category 等。
  - 对裸指针也有偏特化支持。
- 示例（基于 category 进行分派）：
```cpp
// g++ -std=c++17 demo.cpp
#include <iterator>
#include <vector>
#include <list>
#include <iostream>
#include <type_traits>

template <class It>
void advance_impl(It& it, int n, std::random_access_iterator_tag) { it += n; }

template <class It>
void advance_impl(It& it, int n, std::input_iterator_tag) { while (n--) ++it; }

template <class It>
void my_advance(It& it, int n) {
    using cat = typename std::iterator_traits<It>::iterator_category;
    advance_impl(it, n, cat{});
}

int main() {
    std::vector<int> v{1,2,3,4,5};
    auto it = v.begin();
    my_advance(it, 3); // RAIt 快速前进
    std::cout << *it << "\n"; // 4

    std::list<int> l{1,2,3,4,5};
    auto it2 = l.begin();
    my_advance(it2, 3); // input/forward 逐步++前进
    std::cout << *it2 << "\n"; // 4
}
```

---

## 9. 值类别：lvalue、xvalue、glvalue、prvalue
- 标准版本：C++11 重构了值类别（C++17 又改变了 prvalue 的实质化策略）
- 要点：
  - lvalue：有身份，可取地址；xvalue：将亡值；glvalue = lvalue | xvalue；prvalue：纯右值（C++17 后不立即物化临时对象）。
  - 影响重载解析、绑定规则、移动/转发。
- 示例：
```cpp
// g++ -std=c++17 demo.cpp
#include <iostream>
#include <utility>

void cat(int&)      { std::cout << "lvalue\n"; }
void cat(const int&){ std::cout << "const lvalue\n"; }
void cat(int&&)     { std::cout << "rvalue\n"; }

int&& make_rr() { static int x=0; return std::move(x); } // xvalue（注意危险示例）

int main() {
    int i = 0;
    cat(i);              // lvalue
    cat(std::move(i));   // rvalue（xvalue -> 绑定到 int&& 重载）
    cat(42);             // prvalue -> 绑定到 const int& 或 int&&，此处选择 int&&
}
```

---

## 10. 移动语义
- 标准版本：C++11
- 要点：
  - 提供移动构造/赋值以转移资源所有权，避免拷贝开销。
  - 与 noexcept 移动构造配合，容器能更积极地优化（如 vector 扩容移动）。
- 示例：
```cpp
// g++ -std=c++17 demo.cpp
#include <iostream>
#include <cstring>

struct Buffer {
    size_t n{};
    char* p{};

    Buffer() = default;
    explicit Buffer(size_t n): n(n), p(new char[n]) {}

    // 拷贝
    Buffer(const Buffer& rhs): n(rhs.n), p(new char[n]) { std::memcpy(p, rhs.p, n); }
    Buffer& operator=(const Buffer& rhs) {
        if (this != &rhs) { Buffer tmp(rhs); swap(tmp); }
        return *this;
    }
    // 移动
    Buffer(Buffer&& rhs) noexcept : n(rhs.n), p(rhs.p) { rhs.n = 0; rhs.p = nullptr; }
    Buffer& operator=(Buffer&& rhs) noexcept {
        if (this != &rhs) { delete[] p; n = rhs.n; p = rhs.p; rhs.n = 0; rhs.p = nullptr; }
        return *this;
    }
    ~Buffer(){ delete[] p; }

    void swap(Buffer& other) noexcept { std::swap(n, other.n); std::swap(p, other.p); }
};

int main() {
    Buffer a(1024);
    Buffer b = std::move(a); // 移动构造
    std::cout << b.n << "\n"; // 1024
}
```

---

## 11. 转发引用（forwarding reference，俗称“万能引用”）
- 标准版本：C++11（术语在后续标准文本中完善）
- 要点：
  - 形式为 T&& 且 T 由推导得出时；能绑定到左/右值，保持值类别信息。
  - 常与 std::forward 一起用于完美转发。
- 示例：
```cpp
// g++ -std=c++17 demo.cpp
#include <utility>
#include <iostream>

void g(const int&)  { std::cout << "const lvalue\n"; }
void g(int&&)       { std::cout << "rvalue\n"; }

template <class T>
void f(T&& x) { g(std::forward<T>(x)); } // 保持值类别

int main() {
    int a = 0;
    f(a);        // const lvalue
    f(42);       // rvalue
}
```

---

## 12. std::forward<T>() 完美转发
- 标准版本：C++11
- 要点：
  - 保留实参的值类别与 cv 限定，转发给被调用者。
  - 常用于封装/工厂/容器 emplace。
- 示例（简化版工厂）：
```cpp
// g++ -std=c++17 demo.cpp
#include <memory>
#include <utility>

template <class T, class... Args>
std::unique_ptr<T> make(Args&&... args) {
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
}

struct X { X(int, double) {} };

int main() {
    auto p = make<X>(1, 3.14);
}
```

---

## 13. RAII（资源获取即初始化）
- 标准版本：理念自 C++ 早期（C++98 前），语言支撑来自析构、异常传播等
- 要点：
  - 将资源的获取与释放绑定到对象生命周期，异常安全天然良好。
- 示例：
```cpp
// g++ -std=c++17 demo.cpp
#include <cstdio>
#include <stdexcept>

struct File {
    std::FILE* f{};
    explicit File(const char* path, const char* mode) {
        f = std::fopen(path, mode);
        if (!f) throw std::runtime_error("open failed");
    }
    ~File() { if (f) std::fclose(f); }
    std::FILE* get() const { return f; }
};

int main() {
    try {
        File file("demo.txt", "w");
        std::fputs("hello", file.get());
    } catch (...) {}
}
```

---

## 14. 表达式求值顺序（sequencing/evaluation order）
- 标准版本：C++17 显著澄清（但函数实参求值顺序仍未固定）
- 要点：
  - C++17 保证某些运算的求值顺序（如 =、||、&&、?:、<<、>> 左操作数先于右操作数），但函数参数间顺序仍未规定。
  - 对同一标量对象进行未序列化的读/改写会导致未定义行为。
- 示例（不要依赖实参求值顺序）：
```cpp
// g++ -std=c++17 demo.cpp
#include <iostream>

void h(int, int) {}

int main() {
    int i = 0;
    // 未指定：两个实参的求值次序不确定
    h(i++, i++); // 不要写这种代码

    // 明确顺序
    int a = i++; 
    int b = i++;
    h(a, b);
}
```

---

## 15. 弃值表达式（discarded-value expression）
- 标准版本：术语长期存在（C++98 起），在 C++ 标准中用以描述表达式结果被丢弃的情形
- 要点：
  - 如独立的表达式语句 expr;、逗号运算符左侧、static_cast<void>(expr) 等。
  - 常用于显式丢弃返回值/抑制未使用警告。
- 示例：
```cpp
// g++ -std=c++17 demo.cpp
#include <vector>

int main() {
    std::vector<int> v;
    (void)v.capacity();         // 显式丢弃
    v.push_back(1);             // 表达式语句，结果被丢弃
    (void)(v.size() + v.capacity()); // 丢弃复合表达式的值
}
```

---

## 16. 不求值表达式（unevaluated operand）
- 标准版本：C++98 起（sizeof、typeid），C++11 加入 decltype、alignof、noexcept
- 要点：
  - 表达式在编译期检查类型但不计算其值（有少数例外，如 typeid 对多态左值）。
- 示例：
```cpp
// g++ -std=c++17 demo.cpp
#include <type_traits>
#include <iostream>

struct X { int size() const { return 0; } };

template <class T>
auto has_size(int) -> decltype(std::declval<T>().size(), std::true_type{});
template <class>
auto has_size(...) -> std::false_type;

int main() {
    std::cout << std::boolalpha
              << decltype(has_size<X>(0))::value << " "
              << noexcept(sizeof(X)) << "\n"; // true true
}
```

---

## 17. 潜在求值表达式（potentially-evaluated expression）
- 标准版本：C++ 术语（C++11 起更清晰）
- 要点：
  - 不在不求值上下文/丢弃分支的表达式称为潜在求值；常与 if constexpr 对比。
- 示例：
```cpp
// g++ -std=c++17 demo.cpp
#include <type_traits>

template <class T>
void f() {
    if constexpr (std::is_integral_v<T>) {
        (void)sizeof(T); // 不求值
    } else {
        // 这一分支整个不是潜在求值表达式体，不检查其中的 ill-formed 代码
        // int x = "not an int"; // 放开也不会报错（被丢弃）
    }
}

int main() { f<int>(); f<double>(); }
```

---

## 18. 常量表达式（constexpr/consteval/constinit）
- 标准版本：C++11（constexpr）、C++14（放宽）、C++20（consteval/constinit、更多语句可 constexpr）、C++23（进一步补强）
- 要点：
  - constexpr 函数/变量可在编译期求值；consteval 必须在编译期；constinit 保证静态存储期对象常量初始化但并非常量。
- 示例：
```cpp
// g++ -std=c++20 demo.cpp
#include <array>
#include <iostream>

constexpr int fact(int n) {
    int r = 1; for (int i=2;i<=n;++i) r*=i; return r;
}
consteval int sq(int x) { return x*x; }
constinit int g = 42; // 静态期常量初始化

int main() {
    static_assert(fact(5) == 120);
    constexpr int s = sq(7);
    std::cout << s << " " << g << "\n";
}
```

---

## 19. 临时量实质化（Temporary Materialization）
- 标准版本：C++17
- 要点：
  - C++17 起 prvalue 不立即对每一步都物化临时对象；在需要时才“实质化”。
  - 直接影响示例：可绑定到子对象引用。
- 示例（C++17 前非法，C++17 起合法）：
```cpp
// g++ -std=c++17 demo.cpp
#include <iostream>

struct S { int x; };

int main() {
    const int& r = S{42}.x; // C++17 起 OK：整体临时 S 实质化，x 引用延长
    std::cout << r << "\n";
}
```

---

## 20. 标准布局类（standard-layout）
- 标准版本：C++11（将 POD 分解为标准布局与可平凡等概念）
- 要点（简化）：
  - 不含虚函数/虚基类；所有非静态数据成员有相同访问控制；首个非静态成员类型在继承层次中限制；无重复基类等。
  - 可在与 C 交互时用于内存布局保证（配合 is_standard_layout）。
- 示例：
```cpp
// g++ -std=c++17 demo.cpp
#include <type_traits>
#include <iostream>

struct A { int x; double y; };           // 标准布局
struct B { virtual void f(); int x; };   // 非标准布局（有虚函数）

int main() {
    std::cout << std::boolalpha
              << std::is_standard_layout_v<A> << " "
              << std::is_standard_layout_v<B> << "\n"; // true false
}
```

---

## 21. 编译期 constexpr 元编程算法（汉诺塔/递归/字符拼接/函数表）
- 标准版本：C++11 起（constexpr），C++14/17 显著增强
- 示例（编译期生成汉诺塔步骤字符串）：
```cpp
// g++ -std=c++20 demo.cpp
#include <array>
#include <string_view>
#include <utility>

constexpr void hanoi_impl(int n, char A, char B, char C, std::string& out) {
    if (n==0) return;
    hanoi_impl(n-1, A, C, B, out);
    out += A; out += '>'; out += C; out += ';';
    hanoi_impl(n-1, B, A, C, out);
}

constexpr auto hanoi(int n) {
    std::string out;
    out.reserve((1<<n)-1 * 3);
    hanoi_impl(n, 'A','B','C', out);
    return out; // C++20 允许 std::string 在 constexpr 中使用（实现支持）
}

static_assert(hanoi(3).size() > 0);
```
- 示例（编译期字符数组拼接）：
```cpp
// g++ -std=c++17 demo.cpp
#include <array>
#include <utility>

template <size_t N, size_t M>
constexpr auto concat(const char (&a)[N], const char (&b)[M]) {
    std::array<char, N+M-1> r{};
    for (size_t i=0;i<N-1;++i) r[i]=a[i];
    for (size_t j=0;j<M;++j)  r[N-1+j]=b[j];
    return r;
}
static_assert(concat("ab","cd")[3]=='d');
```
- 示例（编译期“打函数表”）：
```cpp
// g++ -std=c++17 demo.cpp
#include <array>
#include <iostream>

using Fn = int(*)(int);
constexpr int add1(int x){ return x+1; }
constexpr int mul2(int x){ return x*2; }

constexpr std::array<Fn,2> table{ add1, mul2 };

int main(){ std::cout << table[1](10) << "\n"; } // 20
```

---

## 22. 用户定义字面量（UDL）
- 标准版本：C++11（自定义后缀），C++14 加强，C++20/23 标准库补充更多 UDL（如 chrono）
- 示例：
```cpp
// g++ -std=c++17 demo.cpp
#include <iostream>
#include <chrono>

constexpr long long operator"" _kg(unsigned long long v) { return static_cast<long long>(v*1000); }

using namespace std::chrono_literals;

int main(){
    std::cout << 3_kg << " grams\n";     // 3000 grams
    auto t = 150ms;                      // 标准库 UDL
    std::cout << t.count() << "ms\n";
}
```

---

## 23. PIMPL（指针指向实现）
- 标准版本：设计模式，与语言版本无关（建议用 C++11 的 unique_ptr 管理）
- 要点：
  - 隐藏实现细节，降低编译依赖，加快构建。
- 示例（文件切分示意）：
```cpp
// g++ -std=c++17 demo.cpp
// ----- widget.h -----
#include <memory>
class Widget {
public:
    Widget();
    ~Widget();
    void draw() const;
private:
    struct Impl;
    std::unique_ptr<Impl> pimpl;
};

// ----- widget.cpp -----
#include <iostream>
struct Widget::Impl { void draw() const { std::cout << "drawing\n"; } };
Widget::Widget(): pimpl(std::make_unique<Impl>()) {}
Widget::~Widget() = default;
void Widget::draw() const { pimpl->draw(); }

// ----- main.cpp -----
int main(){ Widget w; w.draw(); }
```

---

## 24. 三五零原则（Rule of Three/Five/Zero）
- 标准版本：Rule of Three（C++03），Rule of Five（C++11），Rule of Zero（现代 C++）
- 要点：
  - 三：自写析构/拷构/拷赋需成组出现。
  - 五：再加移动构造/移动赋值。
  - 零：尽量用 RAII 组合，避免自写这五个特殊成员。
- 示例（Rule of Five 已示于 Buffer；Rule of Zero 示例）：
```cpp
// g++ -std=c++17 demo.cpp
#include <vector>
#include <string>

struct Log { std::vector<std::string> lines; // 组合类型，零规则
    void add(std::string s){ lines.push_back(std::move(s)); }
}; // 不需要自己写析构/拷贝/移动
```

---

## 25. 构造函数异常处理与异常安全
- 标准版本：C++98 起（异常），C++11 引入 noexcept 指示
- 要点：
  - 构造函数抛出时，已构造完成的成员会按逆序析构；未构造的不会析构。
  - strong/basic/nothrow 保证；为移动构造标注 noexcept 可提升容器优化。
- 示例：
```cpp
// g++ -std=c++17 demo.cpp
#include <string>
#include <vector>

struct A { A() {} ~A() {} };
struct B {
    B() { throw 42; }
    ~B() {}
};
struct C {
    A a;
    B b;  // 这里抛出，a 会被析构
    C() {}
};

int main() {
    try { C c; } catch (...) {}
}
```

---

## 26. 函数 try 块（function try-block）
- 标准版本：C++98 起
- 要点：
  - 可包裹构造函数的初始化列表和函数体，用于捕获构造期间异常并转换/记录后再抛。
- 示例：
```cpp
// g++ -std=c++17 demo.cpp
#include <iostream>
#include <stdexcept>

struct S {
    S() try : S(0) { /* 主体 */ }
    catch(...) { std::cerr << "ctor failed\n"; throw; }

    explicit S(int x) {
        if (x==0) throw std::runtime_error("bad");
    }
};

int main(){ try{ S s; } catch(...){} }
```

---

## 27. 模块（Modules）
- 标准版本：C++20
- 要点：
  - 用 export module / import 隔离可见性与 ODR，减少宏/包含的负担，加速构建。
- 示例：
```cpp
// g++ -std=c++20 demo.cpp  （编译器需支持模块）
/*** math.mpp ***/
export module math;
export int add(int a, int b) { return a+b; }

/*** main.cpp ***/
import math;
#include <iostream>
int main(){ std::cout << add(1,2) << "\n"; }
```

---

## 28. 全局模块片段（global module fragment）及意义
- 标准版本：C++20
- 要点：
  - 形如 module; 的片段位于模块声明之前，允许引入传统头（宏/包含）影响本模块实现但不导出。
- 示例：
```cpp
// g++ -std=c++20 demo.cpp
/*** m.mpp ***/
module;               // 全局模块片段开始
#include <cmath>      // 仅影响当前实现单元
export module m;
export double sqr(double x){ return std::pow(x,2); }
```

---

## 29. 模块分区（module partition）
- 标准版本：C++20
- 要点：
  - module M:part 定义内部可复用的分区；可 export import :part 以导出。
- 示例：
```cpp
// g++ -std=c++20 demo.cpp
/*** calc_part.mpp ***/
export module calc:util;
export int inc(int x){ return x+1; }

/*** calc.mpp ***/
export module calc;
export import :util;     // 导出分区
export int add1(int x){ return inc(x); }

/*** main.cpp ***/
import calc;
#include <iostream>
int main(){ std::cout << add1(41) << "\n"; }
```

---

## 30. 在 CMake 工程中声明模块
- 要点：
  - CMake 3.28 起，使用 FILE_SET CXX_MODULES 声明模块单元。
  - 设置 CMAKE_CXX_STANDARD 为 20/23，并使用支持模块的编译器。
- 示例（CMakeLists.txt）：
```cmake
cmake_minimum_required(VERSION 3.28)
project(mod_demo CXX)
set(CMAKE_CXX_STANDARD 20)

add_library(mylib)
target_sources(mylib
  PUBLIC
    FILE_SET CXX_MODULES FILES
      src/calc.mpp
      src/calc_part.mpp
)

add_executable(app src/main.cpp)
target_link_libraries(app PRIVATE mylib)
```

---

## 31. 范围库（Ranges）：适配器、CPO、niebloid、ADL、工厂、视图、迭代器对 vs 哨位
- 标准版本：C++20（C++23 新增多种视图/适配器）
- 要点：
  - 适配器：views::filter/transform/take/drop/join/split 等；C++23：views::repeat、chunk_by 等。
  - CPO（定制点对象）/niebloid：如 ranges::begin/ranges::size 是不可意外 ADL 的函数对象；内部通过 ADL 定位自定义 begin/end。
  - 工厂：views::iota/single/empty/repeat(23)/iota(闭区间 iota_view 不在标准)。
  - 视图（view）是轻量、懒惰的不可拥有或条件拥有的 range，常通过 view_interface CRTP 复用接口。
  - 迭代器+哨位（sentinel）替代早期的迭代器成对，允许 end 不是同型迭代器，更高效。
- 示例（基本管道）：
```cpp
// g++ -std=c++20 demo.cpp
#include <ranges>
#include <vector>
#include <iostream>

int main() {
    std::vector<int> v{1,2,3,4,5,6};
    auto rng = v | std::views::filter([](int x){ return x%2; })
                 | std::views::transform([](int x){ return x*x; });

    for (int x : rng) std::cout << x << " "; // 1 9 25
}
```
- 示例（自定义视图：计数范围，展示 sentinel）：
```cpp
// g++ -std=c++20 demo.cpp
#include <ranges>
#include <iostream>

struct counter_view : std::ranges::view_interface<counter_view> {
    struct iter {
        int cur{};
        using difference_type = std::ptrdiff_t;
        using value_type = int;
        int operator*() const { return cur; }
        iter& operator++(){ ++cur; return *this; }
        void operator++(int){ ++cur; }
        friend bool operator==(const iter& a, const iter& b){ return a.cur==b.cur; }
    };
    struct sentinel { int last{}; friend bool operator==(const iter& i, const sentinel& s){ return i.cur==s.last; } };
    int first{}, last{};
    iter begin() const { return {first}; }
    sentinel end() const { return {last}; }
};

int main(){
    for (int x : counter_view{1,5}) std::cout << x << " "; // 1 2 3 4
}
```

---

## 32. 为什么仿函数对象的 operator() 常要求加 const
- 标准版本：与算法/概念契约相关（C++98 命名要求；C++20 Ranges 概念如 regular_invocable<const F&, ...>）
- 要点：
  - 算法通常以 const 上下文持有并调用函数对象（如存入 const 局部/成员），因此要求 operator() 可在 const 对象上调用。
  - Ranges 概念 regular_invocable 明确要求能以 const F& 调用。
- 示例：
```cpp
// g++ -std=c++20 demo.cpp
#include <algorithm>
#include <vector>
#include <iostream>

struct CmpBad { bool operator()(int a, int b) { return a<b; } };        // 缺 const
struct CmpGood{ bool operator()(int a, int b) const { return a<b; } };  // 正确

int main(){
    std::vector<int> v{3,1,2};
    // std::sort(v.begin(), v.end(), CmpBad{}); // 可能失败：需要 const 调用
    std::sort(v.begin(), v.end(), CmpGood{});
    for(int x: v) std::cout<<x<<" ";
}
```

---

## 33. CRTP（奇特重复模板模式）在 Ranges 中的应用
- 标准版本：设计模式；Ranges 提供 view_interface（C++20）
- 要点：
  - 子类以自身类型作为模板实参继承基类：struct D : B<D>。
  - Ranges 的 view_interface 提供 size/empty/front/back 等默认实现，派生类只需提供 begin/end。
- 示例：
```cpp
// g++ -std=c++20 demo.cpp
#include <ranges>
#include <vector>
#include <iostream>

struct my_view : std::ranges::view_interface<my_view> {
    std::vector<int> data;
    my_view(std::initializer_list<int> il): data(il) {}
    auto begin() const { return data.begin(); }
    auto end()   const { return data.end(); }
};

int main(){
    my_view v{1,2,3};
    std::cout << v.front() << " " << v.back() << " size=" << v.size() << "\n";
}
```

---

## 34. requires 子句
- 标准版本：C++20
- 要点：
  - 为模板形参添加约束；参与重载决议与部分排序。
- 示例：
```cpp
// g++ -std=c++20 demo.cpp
#include <ranges>
#include <iostream>

template <std::ranges::input_range R>
void print(R&& r){
    for (auto&& x : r) std::cout << x << " ";
    std::cout << "\n";
}

int main(){ int a[]{1,2,3}; print(a); }
```

---

## 35. 约束的归入（subsumption）
- 标准版本：C++20
- 要点：
  - 一个约束 A subsumes 约束 B，当 A 更强（蕴含）于 B；用于选择最特化模板。
- 示例：
```cpp
// g++ -std=c++20 demo.cpp
#include <concepts>
#include <iostream>

template <std::integral T>
void foo(T){ std::cout<<"integral\n"; }

template <std::signed_integral T>
void foo(T){ std::cout<<"signed integral\n"; }

int main(){
    foo(42u);  // integral
    foo(-1);   // signed integral（更强约束优先）
}
```

---

## 36. 约束的偏序（partial ordering with constraints）
- 标准版本：C++20
- 要点：
  - 约束是重载/特化选择的一部分；结合常规模板偏序决定最佳匹配。
- 示例：
```cpp
// g++ -std=c++20 demo.cpp
#include <concepts>
#include <iostream>

template <class T>
requires std::integral<T> || std::floating_point<T>
void bar(T){ std::cout<<"arithmetic\n"; }

template <std::integral T>
void bar(T){ std::cout<<"integral only\n"; }

int main(){
    bar(3);    // integral only
    bar(3.14); // arithmetic
}
```

---

## 37. concept（概念）
- 标准版本：C++20
- 要点：
  - 为类型性质定义可组合的布尔谓词，参与模板约束/诊断更清晰。
- 示例：
```cpp
// g++ -std=c++20 demo.cpp
#include <concepts>
#include <string>
#include <iostream>

template <class T>
concept StringLike = requires(T t) {
    { t.size() } -> std::convertible_to<std::size_t>;
    { t.data() } -> std::convertible_to<const char*>;
};

template <StringLike S>
void print(S s){ std::cout << s.data() << " ("<< s.size() << ")\n"; }

int main(){ print(std::string("hi")); }
```

---

## 38. 原子约束（atomic constraints）
- 标准版本：C++20
- 要点：
  - 概念与 requires 表达式被规范化为“原子约束”后进行比较与满足性判断。
  - 开发者通常无需显式操作原子约束，只需编写清晰的 requires/概念。
- 示例（展示不同原子约束组合）：
```cpp
// g++ -std=c++20 demo.cpp
#include <concepts>
#include <type_traits>

template <class T>
concept SmallIntegral = std::integral<T> && (sizeof(T) <= sizeof(int));

static_assert(SmallIntegral<short>);
static_assert(!SmallIntegral<long long>);
```

---

## 39. 约束规范化过程（normalization）
- 标准版本：C++20
- 要点（理解层面）：
  - 编译器将 requires、概念、布尔逻辑化为一组原子约束并化简，用于 subsumption/偏序判断。
  - 实际编码中关注“可读的概念定义”和“避免过度复杂的 requires 表达式”。

---

## 40. Ranges 中常用概念：indirectly_readable / indirectly_writable 等
- 标准版本：C++20
- 要点：
  - indirectly_readable<In>：从迭代器解引用可读值类型。
  - indirectly_writable<Out, T>：可将 T 写入由迭代器 Out 指向的对象。
- 示例（简单算法使用概念约束迭代器类型）：
```cpp
// g++ -std=c++20 demo.cpp
#include <concepts>
#include <iterator>
#include <iostream>

template <std::indirectly_readable In, std::indirectly_writable<std::iter_reference_t<In>, int> Out>
void copy_to_int(In first, In last, Out out) {
    for (; first!=last; ++first, ++out) *out = static_cast<int>(*first);
}

int main(){
    int a[]{1,2,3}; int b[3]{};
    copy_to_int(a, a+3, b);
    for(int x: b) std::cout << x << " ";
}
```

---

## 41. 协程（coroutines）概览
- 标准版本：C++20
- 要点：
  - 关键字：co_await、co_yield、co_return。
  - 需要 promise_type、自定义 awaiter/awaitable。
- 示例（最小 task，立即完成）：
```cpp
// g++ -std=c++20 demo.cpp
#include <coroutine>
#include <iostream>

struct task {
    struct promise_type {
        task get_return_object(){ return {}; }
        std::suspend_never initial_suspend(){ return {}; }
        std::suspend_never final_suspend() noexcept { return {}; }
        void return_void() {}
        void unhandled_exception() { std::terminate(); }
    };
};

task hello() {
    std::cout << "hello\n";
    co_return;
}

int main(){ hello(); }
```

---

## 42. 协程 promise_type 细节
- 标准版本：C++20
- 要点：
  - 决定返回对象、初末挂起点、异常处理、返回值等。
- 示例（返回一个能取值的简单协程类型）：
```cpp
// g++ -std=c++20 demo.cpp
#include <coroutine>
#include <optional>
#include <iostream>

struct value_task {
    struct promise_type {
        std::optional<int> value;
        value_task get_return_object() { return value_task{ std::coroutine_handle<promise_type>::from_promise(*this) }; }
        std::suspend_never initial_suspend(){ return {}; }
        std::suspend_always final_suspend() noexcept { return {}; }
        void return_value(int v){ value = v; }
        void unhandled_exception(){ std::terminate(); }
    };
    std::coroutine_handle<promise_type> h;
    ~value_task(){ if (h) h.destroy(); }
    int result() { return *h.promise().value; }
};

value_task gen() { co_return 42; }

int main(){ auto t = gen(); std::cout << t.result() << "\n"; }
```

---

## 43. 挂起点（suspend points）
- 标准版本：C++20
- 要点：
  - co_await expr：等待体；co_yield expr：生成值并挂起；co_return：结束协程。
  - initial_suspend/final_suspend 控制协程开始/结束是否先挂起。
- 示例（co_yield 生成若干值）：
```cpp
// g++ -std=c++20 demo.cpp
#include <coroutine>
#include <iostream>
#include <optional>

template <class T>
struct generator {
    struct promise_type {
        T current;
        generator get_return_object(){ return generator{ std::coroutine_handle<promise_type>::from_promise(*this) }; }
        std::suspend_always initial_suspend(){ return {}; }
        std::suspend_always final_suspend() noexcept { return {}; }
        std::suspend_always yield_value(T v){ current = v; return {}; }
        void return_void() {}
        void unhandled_exception(){ std::terminate(); }
    };
    std::coroutine_handle<promise_type> h;
    ~generator(){ if (h) h.destroy(); }
    bool next(){ if (!h.done()) { h.resume(); } return !h.done(); }
    T value() const { return h.promise().current; }
};

generator<int> seq(int n){
    for (int i=0;i<n;++i) co_yield i;
}

int main(){
    auto g = seq(3);
    while (g.next()) std::cout << g.value() << " "; // 0 1 2
}
```

---

## 44. 等待体（awaitable/awaiter）
- 标准版本：C++20
- 要点：
  - awaitable 是能被 co_await 的对象；其 awaiter 需提供 await_ready/await_suspend/await_resume。
- 示例（自定义 awaiter，延迟 1 次恢复）：
```cpp
// g++ -std=c++20 demo.cpp
#include <coroutine>
#include <iostream>

struct once_awaitable {
    bool awaited = false;
    bool await_ready() const noexcept { return false; }
    void await_suspend(std::coroutine_handle<> h) noexcept {
        if (!awaited) { // 第一次挂起后直接恢复
            const_cast<once_awaitable*>(this)->awaited = true;
            h.resume();
        }
    }
    void await_resume() const noexcept {}
};

struct task {
    struct promise_type {
        task get_return_object(){ return {}; }
        std::suspend_never initial_suspend(){ return {}; }
        std::suspend_never final_suspend() noexcept { return {}; }
        void return_void() {}
        void unhandled_exception(){ std::terminate(); }
    };
};

task run() {
    co_await once_awaitable{};
    std::cout << "resumed\n";
}

int main(){ run(); } // resumed
```

---

## 45. 范围生成器（用协程实现 range-like 生成）
- 标准版本：C++20（协程），范围接口需自行实现（标准尚无 std::generator）
- 示例（把前述 generator 适配成可用于 range-for 的输入范围）：
```cpp
// g++ -std=c++20 demo.cpp
#include <coroutine>
#include <iterator>
#include <iostream>

template <class T>
struct generator {
    struct promise_type {
        T current;
        generator get_return_object(){ return generator{ std::coroutine_handle<promise_type>::from_promise(*this) }; }
        std::suspend_always initial_suspend(){ return {}; }
        std::suspend_always final_suspend() noexcept { return {}; }
        std::suspend_always yield_value(T v){ current = v; return {}; }
        void return_void() {}
        void unhandled_exception(){ std::terminate(); }
    };
    std::coroutine_handle<promise_type> h;
    generator(std::coroutine_handle<promise_type> h): h(h) {}
    generator(generator&& o): h(std::exchange(o.h, {})) {}
    ~generator(){ if (h) h.destroy(); }

    struct iter {
        std::coroutine_handle<promise_type> h;
        bool done = false;
        using value_type = T;
        using difference_type = std::ptrdiff_t;
        iter& operator++(){ h.resume(); done = h.done(); return *this; }
        const T& operator*() const { return h.promise().current; }
        bool operator==(std::default_sentinel_t) const { return done; }
    };

    iter begin(){ h.resume(); return {h, h.done()}; }
    std::default_sentinel_t end() { return {}; }
};

generator<int> counter(int n){ for(int i=0;i<n;++i) co_yield i; }

int main(){
    for (int x : counter(5)) std::cout << x << " "; // 0 1 2 3 4
}
```

---

## 46. 协程抛异常
- 标准版本：C++20
- 要点：
  - 协程体未捕获异常会调用 promise_type::unhandled_exception。
  - 可在 promise 中存储 exception_ptr 并在 resume/结果获取时重新抛出。
- 示例：
```cpp
// g++ -std=c++20 demo.cpp
#include <coroutine>
#include <exception>
#include <iostream>

struct task {
    struct promise_type {
        std::exception_ptr ep;
        task get_return_object(){ return task{ std::coroutine_handle<promise_type>::from_promise(*this) }; }
        std::suspend_never initial_suspend(){ return {}; }
        std::suspend_never final_suspend() noexcept { return {}; }
        void unhandled_exception(){ ep = std::current_exception(); }
        void return_void(){}
    };
    std::coroutine_handle<promise_type> h;
    ~task(){ if (h) { if (h.promise().ep) { try { std::rethrow_exception(h.promise().ep); } catch(const std::exception& e){ std::cerr << "caught: " << e.what() << "\n"; } } h.destroy(); } }
};

task boom(){
    throw std::runtime_error("fail");
    co_return;
}

int main(){ boom(); }
```

---

## 47. 格式化器特化（std::formatter 特化）
- 标准版本：C++20 <format>，C++23 增强（std::print）
- 要点：
  - 为用户类型特化 std::formatter<T> 以支持 std::format/std::print。
- 示例：
```cpp
// g++ -std=c++20 demo.cpp
#include <format>
#include <iostream>

struct Point { int x,y; };

template <>
struct std::formatter<Point> : std::formatter<std::string_view> {
    // 复用字符串格式说明解析
    auto format(const Point& p, std::format_context& ctx) const {
        return std::format_to(ctx.out(), "({}, {})", p.x, p.y);
    }
};

int main(){
    Point p{1,2};
    std::cout << std::format("p = {}\n", p);
}
```

---

## 48. 基本格式化器与格式化 API
- 标准版本：C++20（format），C++23（print）
- 要点：
  - 占位符 {}，支持格式说明：{:<8}, {:>8}, {:^8}, {:#x}, {:.3f}, {:%Y-%m-%d}（与 chrono）。
  - format_to / vformat / print（C++23）。
- 示例：
```cpp
// g++ -std=c++20 demo.cpp
#include <format>
#include <iostream>
#include <chrono>

int main(){
    std::cout << std::format("|{:<8}|{:>8}|{:^8}|\n", "L", 42, "mid");
    std::cout << std::format("{:#x} {:.2f}\n", 255, 3.14159);

    using namespace std::chrono;
    auto tp = sys_days{2024y/12/31};
    std::cout << std::format("{:%Y-%m-%d}\n", tp);
}
```

---

## 49. 格式串格式（format string grammar）要点
- 标准版本：C++20
- 要点：
  - 一般形式：{[arg-id][:format-spec]}，format-spec 包含对齐、填充、宽度、精度、类型等。
  - 安全性：格式说明与参数类型检查由库完成（运行期检查；C++26 提案在推进 constexpr 检查）。
- 示例（见上一节）。

---

## 50. 显式对象形参（Deducing this，显式 this 形参）
- 标准版本：C++23
- 要点：
  - 允许将 this 写成显式第一个形参：void f(this T& self, ...)，支持重载与完美转发/值类别保持。
- 示例：
```cpp
// g++ -std=c++23 demo.cpp
#include <iostream>
struct Vec {
    int x{};
    void inc(this Vec& self, int dx){ self.x += dx; }
    int  get(this const Vec& self) { return self.x; }
};
int main(){
    Vec v{1};
    v.inc(3);
    std::cout << v.get() << "\n"; // 4
}
```

---

# 额外重要特性与技术点（面试高频）

## 51. 智能指针：unique_ptr / shared_ptr / weak_ptr
- 标准版本：C++11
- 要点：
  - unique_ptr 独占所有权（可移动不可拷贝）；shared_ptr 共享所有权；weak_ptr 观测不参与计数。
- 示例：
```cpp
// g++ -std=c++17 demo.cpp
#include <memory>
#include <iostream>

struct X{ ~X(){ std::cout<<"bye\n"; } };

int main(){
    auto p = std::make_unique<X>();
    auto sp = std::shared_ptr<X>(std::move(p.release())); // 演示转换（实际应直接 make_shared）
    std::weak_ptr<X> wp = sp;
    std::cout << wp.use_count() << "\n"; // 1
}
```

---

## 52. noexcept 与异常规范
- 标准版本：C++11（noexcept）、C++17（条件 noexcept 在标准库中运用更广）
- 要点：
  - noexcept(true/false) 与 noexcept(expr) 检查；影响优化与异常传播。
  - 移动构造标 noexcept 有利容器移动而非拷贝。
- 示例：
```cpp
// g++ -std=c++17 demo.cpp
#include <type_traits>
#include <iostream>

struct M {
    M() {}
    M(M&&) noexcept {}     // 容器更愿意移动
};
static_assert(noexcept(M(std::declval<M&&>())));

int main(){ std::cout << "ok\n"; }
```

---

## 53. 三路比较（<=>）与默认比较
- 标准版本：C++20
- 要点：
  - 合成比较，自动生成 ==、<、<= 等；可选择强/弱序。
- 示例：
```cpp
// g++ -std=c++20 demo.cpp
#include <compare>
#include <iostream>

struct P {
    int x; double y;
    auto operator<=>(const P&) const = default; // 全量成员比较
};

int main(){
    P a{1,2}, b{1,3};
    std::cout << std::boolalpha << (a < b) << "\n"; // true
}
```

---

## 54. optional / variant / any / expected
- 标准版本：optional/variant/any（C++17），expected（C++23）
- 要点：
  - optional：可空值；variant：类型安全的联合；any：类型擦除；expected：返回值 + 错误。
- 示例（expected）：
```cpp
// g++ -std=c++23 demo.cpp
#include <expected>
#include <string>
#include <charconv>
#include <iostream>

std::expected<int, std::string> to_int(std::string_view s){
    int v{};
    auto [p, ec] = std::from_chars(s.data(), s.data()+s.size(), v);
    if (ec != std::errc{}) return std::unexpected("parse error");
    return v;
}

int main(){
    auto e = to_int("42");
    if (e) std::cout << *e << "\n"; else std::cout << e.error() << "\n";
}
```

---

## 55. string_view / span
- 标准版本：string_view（C++17），span（C++20）
- 要点：
  - 非拥有视图，避免拷贝；注意生存期。
- 示例：
```cpp
// g++ -std=c++20 demo.cpp
#include <string_view>
#include <span>
#include <iostream>

void print(std::string_view sv){ std::cout << sv << "\n"; }
void sum(std::span<const int> s){ int r=0; for(int x: s) r+=x; std::cout<<r<<"\n"; }

int main(){
    std::string s = "hello";
    print(s); // ok

    int a[]{1,2,3};
    sum(a);   // ok
}
```

---

## 56. 文件系统（std::filesystem）
- 标准版本：C++17
- 要点：
  - path、directory_iterator、copy/move/remove 等。
- 示例：
```cpp
// g++ -std=c++17 demo.cpp -lstdc++fs (旧编译器需要)
// 现代编译器不再需要单独链接
#include <filesystem>
#include <iostream>

int main(){
    namespace fs = std::filesystem;
    fs::path p = "demo";
    fs::create_directory(p);
    std::cout << fs::exists(p) << "\n";
    fs::remove(p);
}
```

---

## 57. 并发与同步：jthread/stop_token、latch/barrier
- 标准版本：C++11（thread/mutex/condition_variable/atomic），C++20（jthread/stop_token/latch/barrier），C++23（更多增强）
- 要点：
  - jthread 自动 join；stop_token 协作式取消；latch/barrier 控制批次同步。
- 示例：
```cpp
// g++ -std=c++20 demo.cpp
#include <thread>
#include <stop_token>
#include <chrono>
#include <iostream>

void worker(std::stop_token st){
    while(!st.stop_requested()){
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
    std::cout << "stopped\n";
}

int main(){
    std::jthread t(worker);
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    t.request_stop(); // 协作取消
}
```

---

## 58. 原子与内存序（std::atomic）
- 标准版本：C++11 起
- 要点：
  - memory_order：relaxed、acquire/release、acq_rel、seq_cst；面试常考“释放-获取建立 happens-before”。
- 示例（简单 acquire-release）：
```cpp
// g++ -std=c++17 demo.cpp
#include <atomic>
#include <thread>
#include <cassert>

std::atomic<int> data{0};
std::atomic<bool> flag{false};

int main(){
    std::thread t1([]{
        data.store(42, std::memory_order_relaxed);
        flag.store(true, std::memory_order_release);
    });
    std::thread t2([]{
        while(!flag.load(std::memory_order_acquire)) {}
        assert(data.load(std::memory_order_relaxed) == 42);
    });
    t1.join(); t2.join();
}
```

---

## 59. 保证性拷贝省略（guaranteed copy elision）
- 标准版本：C++17
- 要点：
  - 某些情形（返回临时、直接初始化临时等）强制不创建中间临时对象，构造直接发生于目标处。
- 示例：
```cpp
// g++ -std=c++17 demo.cpp
#include <iostream>

struct X {
    X(){ std::cout<<"X()\n"; }
    X(const X&){ std::cout<<"copy\n"; }
    X(X&&){ std::cout<<"move\n"; }
};

X make(){ return X{}; } // C++17 起不需要临时移动/拷贝

int main(){ X x = make(); } // 只打印 X()
```

---

## 60. 时间库增强：calendar/time zones 与 chrono 格式化
- 标准版本：C++20
- 要点：
  - civil calendar、时区数据库、chrono 格式化支持。
- 示例（基础格式化见第 48 节）。

---

# 小贴士（汇总建议）
- 熟练掌握值类别、移动/转发和完美转发的交互；能现场写出 forwarding 构造/工厂。
- SFINAE 与 concepts：能写出简单 requires 子句，知道 subsumption 的选择规则。
- Ranges：会用常见 views 管道，并能说出 view 的懒惰与生存期注意点；知道 iterator+sentinel 的优势。
- 模块与 CMake：知道 global module fragment 的用途（兼容宏/旧头），能写出最小可用的模块工程。
- 协程：能解释 promise_type、挂起点、异常处理；会写一个最小 generator。
- 格式化：会给 struct 特化 formatter。
- 异常与 noexcept：理解容器为何偏好 noexcept move；能说出 strong/basic 保证。
- 规则三/五/零：能根据资源管理场景选择正确策略（倾向零原则 + 组合）。

如果你希望，我可以把以上内容导出成单一 Markdown 文件（含目录与交叉链接），或根据你的目标岗位（系统/嵌入式/服务端/高频交易）定制精简版重点清单与练习题。