> 作者：莲子粥
链接：https://www.zhihu.com/question/451327108/answer/3299498791
来源：知乎
著作权归作者所有。商业转载请联系作者获得授权，非商业转载请注明出处。
>
> 肯定问模板，模板特化，SFINAE，type_traits，形参包，结构化绑定及其手搓，具名要求，迭代器trait，值类别，左右值、泛左值(glvalue)、纯右值(prvalue)，移动语义，转发引用(俗称万能引用)，std::forward<T>()完美转发，RAII，表达式求值，弃值表达式，不求值表达式，潜在求值表达式，常量表达式，临时量实质化(C++17)，标准布局类，用元编程实现constexpr编译期算法(如编译期汉诺塔，编译期递归，拼接字符数组，打函数表)，用户定义字面量，PIMPL，三五零原则，构造函数异常处理，函数 try 块，模块，全局模块片段及其存在的意义，模块分区，在CMake工程中声明模块范围库(范围适配器，定制点对象(CPO)，niebloid，ADL实参依赖查找，常见的范围工厂，视图，老式迭代器对和新式迭代器+哨位概念的对比)，可变仿引用对象的 operator= 成员必须带 const 限定的依据，奇特重现模板模式(CRTP)以及其在C++20范围适配器中的应用概念库，requires子句，约束的归入(subsume)，约束的偏序，concept，原子约束，约束规范化过程，范围库中常用的concept(可间接写入，可间接读取)协程，协程promise_type，挂起点，等待体，范围生成器，协程抛异常，格式化器特化，基本格式化器，格式串格式，显式对象形参(C++23)
>
>我在准备c++的面试，对于这里提到的每一项技术和特性，请给出其具体的c++标准版本（比如c++11），并给出比较详细的特性讲解，帮助我提高c++知识水平和面试技能，同时给出该特性的演示代码，供我学习。要求把这些内容，按序列号，输出为markdown格式，以便我后续导出整理。对于其他这里没有提及，而你认为对于c++从业者或者面试者比较重要的特性和技术点，也请一并罗列讲解并整理。


# C++ 核心特性详解与面试要点

## 1. 模板 (Template)

**标准版本**: C++98/03 引入，C++11/14/17/20 持续增强

**详细讲解**:
模板是C++泛型编程的基础，允许编写与类型无关的代码。模板分为函数模板和类模板，编译器会根据使用的类型生成具体的函数或类（模板实例化）。

**演示代码**:
```cpp
#include <iostream>
#include <vector>

// 函数模板
template<typename T>
T max_value(T a, T b) {
    return (a > b) ? a : b;
}

// 类模板
template<typename T>
class Stack {
private:
    std::vector<T> elements;
public:
    void push(const T& elem) { elements.push_back(elem); }
    T pop() { 
        T elem = elements.back();
        elements.pop_back();
        return elem;
    }
    bool empty() const { return elements.empty(); }
};

int main() {
    std::cout << max_value(10, 20) << std::endl;  // 20
    std::cout << max_value(3.14, 2.71) << std::endl;  // 3.14
    
    Stack<int> intStack;
    intStack.push(7);
    std::cout << intStack.pop() << std::endl;  // 7
    
    return 0;
}
```

## 2. 模板特化 (Template Specialization)

**标准版本**: C++98/03

**详细讲解**:
模板特化允许为特定类型提供定制的模板实现。分为全特化（完全指定所有模板参数）和偏特化（部分指定模板参数）。这是实现类型特定优化和行为的关键技术。

**演示代码**:
```cpp
#include <iostream>
#include <cstring>

// 主模板
template<typename T>
class Storage {
    T data;
public:
    Storage(T val) : data(val) {}
    void print() { std::cout << "Generic: " << data << std::endl; }
};

// 全特化：为 char* 类型特化
template<>
class Storage<char*> {
    char* data;
public:
    Storage(char* val) {
        data = new char[strlen(val) + 1];
        strcpy(data, val);
    }
    ~Storage() { delete[] data; }
    void print() { std::cout << "Specialized for char*: " << data << std::endl; }
};

// 偏特化：为指针类型偏特化
template<typename T>
class Storage<T*> {
    T* data;
public:
    Storage(T* val) : data(val) {}
    void print() { std::cout << "Specialized for pointer: " << *data << std::endl; }
};

int main() {
    Storage<int> s1(42);
    s1.print();  // Generic: 42
    
    char str[] = "Hello";
    Storage<char*> s2(str);
    s2.print();  // Specialized for char*: Hello
    
    int value = 100;
    Storage<int*> s3(&value);
    s3.print();  // Specialized for pointer: 100
    
    return 0;
}
```

## 3. SFINAE (Substitution Failure Is Not An Error)

**标准版本**: C++98/03 引入概念，C++11/14/17 增强

**详细讲解**:
SFINAE 是模板元编程的核心原则。当模板参数替换失败时，编译器不会报错，而是从重载决议集合中移除该候选。这使得我们可以基于类型特性选择不同的实现。C++11 引入 `std::enable_if`，C++17 引入 `if constexpr`，C++20 引入 concepts 作为更现代的替代。

**演示代码**:
```cpp
#include <iostream>
#include <type_traits>

// 使用 SFINAE 区分整数和浮点数
template<typename T>
typename std::enable_if<std::is_integral<T>::value, T>::type
process(T value) {
    std::cout << "Processing integer: " << value << std::endl;
    return value * 2;
}

template<typename T>
typename std::enable_if<std::is_floating_point<T>::value, T>::type
process(T value) {
    std::cout << "Processing float: " << value << std::endl;
    return value * 1.5;
}

// C++17 if constexpr 方式（更清晰）
template<typename T>
T process_v2(T value) {
    if constexpr (std::is_integral_v<T>) {
        std::cout << "Processing integer (v2): " << value << std::endl;
        return value * 2;
    } else if constexpr (std::is_floating_point_v<T>) {
        std::cout << "Processing float (v2): " << value << std::endl;
        return value * 1.5;
    }
}

// 检测成员函数存在性
template<typename T, typename = void>
struct has_size : std::false_type {};

template<typename T>
struct has_size<T, std::void_t<decltype(std::declval<T>().size())>> : std::true_type {};

int main() {
    process(10);        // Processing integer: 10
    process(3.14);      // Processing float: 3.14
    
    process_v2(20);     // Processing integer (v2): 20
    process_v2(2.71);   // Processing float (v2): 2.71
    
    std::cout << "vector has size: " << has_size<std::vector<int>>::value << std::endl;  // 1
    std::cout << "int has size: " << has_size<int>::value << std::endl;  // 0
    
    return 0;
}
```

## 4. type_traits (类型特征)

**标准版本**: C++11 引入，C++14/17/20 持续扩展

**详细讲解**:
`<type_traits>` 提供了一系列编译期类型查询和变换工具。它们是模板元编程的基础设施，用于在编译期获取类型信息、进行类型转换和类型判断。C++17 引入 `_v` 后缀简化语法。

**演示代码**:
```cpp
#include <iostream>
#include <type_traits>
#include <string>

template<typename T>
void analyze_type() {
    std::cout << "Type analysis:" << std::endl;
    std::cout << "  is_integral: " << std::is_integral_v<T> << std::endl;
    std::cout << "  is_floating_point: " << std::is_floating_point_v<T> << std::endl;
    std::cout << "  is_pointer: " << std::is_pointer_v<T> << std::endl;
    std::cout << "  is_const: " << std::is_const_v<T> << std::endl;
    std::cout << "  is_class: " << std::is_class_v<T> << std::endl;
}

// 使用 type_traits 进行类型转换
template<typename T>
void demonstrate_transforms() {
    using NoRef = std::remove_reference_t<T>;
    using NoConst = std::remove_const_t<T>;
    using NoCV = std::remove_cv_t<T>;
    using Ptr = std::add_pointer_t<T>;
    
    std::cout << "Original type same as NoRef: " 
              << std::is_same_v<T, NoRef> << std::endl;
}

// 条件类型选择
template<bool Condition, typename T, typename F>
using conditional_t = typename std::conditional<Condition, T, F>::type;

int main() {
    analyze_type<int>();
    std::cout << std::endl;
    analyze_type<const double*>();
    std::cout << std::endl;
    
    // 条件类型
    using Type = std::conditional_t<true, int, double>;  // int
    std::cout << "Selected type is int: " << std::is_same_v<Type, int> << std::endl;
    
    // 类型转换
    demonstrate_transforms<const int&>();
    
    return 0;
}
```

## 5. 参数包 (Parameter Pack) 和可变参数模板

**标准版本**: C++11

**详细讲解**:
参数包允许模板接受任意数量的模板参数，是实现可变参数模板的基础。通过参数包展开（pack expansion），可以对每个参数执行相同的操作。C++17 的折叠表达式进一步简化了参数包的使用。

**演示代码**:
```cpp
#include <iostream>
#include <string>

// 基础递归展开
void print() {
    std::cout << std::endl;
}

template<typename T, typename... Args>
void print(T first, Args... args) {
    std::cout << first << " ";
    print(args...);  // 递归展开
}

// C++17 折叠表达式
template<typename... Args>
auto sum(Args... args) {
    return (args + ...);  // 一元右折叠
}

template<typename... Args>
void print_v2(Args... args) {
    ((std::cout << args << " "), ...);  // 二元左折叠
    std::cout << std::endl;
}

// 参数包索引访问
template<std::size_t N, typename T, typename... Args>
struct get_nth {
    using type = typename get_nth<N-1, Args...>::type;
};

template<typename T, typename... Args>
struct get_nth<0, T, Args...> {
    using type = T;
};

// 参数包计数
template<typename... Args>
constexpr std::size_t count_args(Args... args) {
    return sizeof...(args);
}

// 完美转发参数包
template<typename... Args>
void forward_to_print(Args&&... args) {
    print(std::forward<Args>(args)...);
}

int main() {
    print(1, 2.5, "hello", 'c');  // 1 2.5 hello c
    
    std::cout << "Sum: " << sum(1, 2, 3, 4, 5) << std::endl;  // 15
    
    print_v2(10, 20, 30);  // 10 20 30
    
    std::cout << "Arg count: " << count_args(1, 2, 3) << std::endl;  // 3
    
    using ThirdType = get_nth<2, int, double, char, float>::type;  // char
    std::cout << "Third type is char: " << std::is_same_v<ThirdType, char> << std::endl;
    
    forward_to_print(100, "forwarded", 3.14);
    
    return 0;
}
```

## 6. 结构化绑定 (Structured Binding)

**标准版本**: C++17

**详细讲解**:
结构化绑定允许将一个对象（如 tuple、pair、struct、array）的成员绑定到多个变量上，使代码更简洁易读。这是现代C++提升代码可读性的重要特性。

**演示代码**:
```cpp
#include <iostream>
#include <tuple>
#include <map>
#include <string>

struct Point {
    int x;
    int y;
};

std::tuple<int, double, std::string> get_student() {
    return {1001, 3.8, "Alice"};
}

int main() {
    // 绑定 tuple
    auto [id, gpa, name] = get_student();
    std::cout << "ID: " << id << ", GPA: " << gpa << ", Name: " << name << std::endl;
    
    // 绑定 struct
    Point p{10, 20};
    auto [x, y] = p;
    std::cout << "Point: (" << x << ", " << y << ")" << std::endl;
    
    // 绑定 array
    int arr[] = {1, 2, 3};
    auto [a, b, c] = arr;
    std::cout << "Array: " << a << ", " << b << ", " << c << std::endl;
    
    // 在循环中使用（特别适合 map）
    std::map<std::string, int> ages = {{"Alice", 25}, {"Bob", 30}};
    for (const auto& [name, age] : ages) {
        std::cout << name << " is " << age << " years old" << std::endl;
    }
    
    // 使用引用修改原值
    auto& [rx, ry] = p;
    rx = 100;
    std::cout << "Modified point.x: " << p.x << std::endl;  // 100
    
    return 0;
}
```

## 7. 手动实现结构化绑定支持

**标准版本**: C++17

**详细讲解**:
要让自定义类型支持结构化绑定，需要提供 `std::tuple_size`、`std::tuple_element` 特化，以及 `get` 函数。这展示了C++标准库如何通过约定实现语言特性的扩展性。

**演示代码**:
```cpp
#include <iostream>
#include <tuple>

// 自定义类
class Person {
    std::string name_;
    int age_;
    double height_;
public:
    Person(std::string name, int age, double height) 
        : name_(name), age_(age), height_(height) {}
    
    const std::string& name() const { return name_; }
    int age() const { return age_; }
    double height() const { return height_; }
};

// 1. 特化 std::tuple_size
namespace std {
    template<>
    struct tuple_size<Person> : std::integral_constant<std::size_t, 3> {};
    
    // 2. 特化 std::tuple_element
    template<>
    struct tuple_element<0, Person> {
        using type = std::string;
    };
    
    template<>
    struct tuple_element<1, Person> {
        using type = int;
    };
    
    template<>
    struct tuple_element<2, Person> {
        using type = double;
    };
}

// 3. 提供 get 函数
template<std::size_t N>
decltype(auto) get(const Person& p) {
    if constexpr (N == 0) return p.name();
    else if constexpr (N == 1) return p.age();
    else if constexpr (N == 2) return p.height();
}

int main() {
    Person p("Alice", 30, 165.5);
    
    // 现在可以使用结构化绑定了
    auto [name, age, height] = p;
    std::cout << "Name: " << name << ", Age: " << age 
              << ", Height: " << height << std::endl;
    
    return 0;
}
```

## 8. 具名要求 (Named Requirements)

**标准版本**: C++98/03 开始，C++20 用 Concepts 正式化

**详细讲解**:
具名要求是C++标准库对类型应满足的语法和语义要求的非正式描述，如 `CopyConstructible`、`MoveAssignable`、`Iterator` 等。C++20 之前这些是文档约定，C++20 后通过 concepts 形式化。

**演示代码**:
```cpp
#include <iostream>
#include <type_traits>
#include <iterator>

// 模拟一些具名要求的检查（C++20之前的方式）

// DefaultConstructible: 必须有默认构造函数
template<typename T, typename = void>
struct is_default_constructible_impl : std::false_type {};

template<typename T>
struct is_default_constructible_impl<T, std::void_t<decltype(T{})>> 
    : std::true_type {};

// CopyConstructible: 可拷贝构造
// MoveConstructible: 可移动构造
// 这些在 <type_traits> 中已有标准实现

class MyClass {
public:
    MyClass() = default;
    MyClass(const MyClass&) = default;
    MyClass(MyClass&&) = default;
    MyClass& operator=(const MyClass&) = default;
    MyClass& operator=(MyClass&&) = default;
};

class NonCopyable {
public:
    NonCopyable() = default;
    NonCopyable(const NonCopyable&) = delete;
    NonCopyable(NonCopyable&&) = default;
};

int main() {
    std::cout << "MyClass is:" << std::endl;
    std::cout << "  DefaultConstructible: " 
              << std::is_default_constructible_v<MyClass> << std::endl;
    std::cout << "  CopyConstructible: " 
              << std::is_copy_constructible_v<MyClass> << std::endl;
    std::cout << "  MoveConstructible: " 
              << std::is_move_constructible_v<MyClass> << std::endl;
    std::cout << "  CopyAssignable: " 
              << std::is_copy_assignable_v<MyClass> << std::endl;
    
    std::cout << "\nNonCopyable is:" << std::endl;
    std::cout << "  CopyConstructible: " 
              << std::is_copy_constructible_v<NonCopyable> << std::endl;  // 0
    std::cout << "  MoveConstructible: " 
              << std::is_move_constructible_v<NonCopyable> << std::endl;  // 1
    
    return 0;
}
```

## 9. 迭代器 Trait

**标准版本**: C++98/03 引入，C++20 大幅改进

**详细讲解**:
迭代器 trait（`std::iterator_traits`）提供了迭代器的类型信息，包括值类型、差值类型、指针类型、引用类型和迭代器类别。这是STL算法能够泛型工作的基础。C++20 引入了新的迭代器概念系统。

**演示代码**:
```cpp
#include <iostream>
#include <iterator>
#include <vector>
#include <list>

// 自定义迭代器
template<typename T>
class SimpleIterator {
    T* ptr_;
public:
    // 必须定义的类型别名
    using iterator_category = std::random_access_iterator_tag;
    using value_type = T;
    using difference_type = std::ptrdiff_t;
    using pointer = T*;
    using reference = T&;
    
    SimpleIterator(T* p) : ptr_(p) {}
    
    reference operator*() const { return *ptr_; }
    pointer operator->() const { return ptr_; }
    SimpleIterator& operator++() { ++ptr_; return *this; }
    SimpleIterator operator++(int) { SimpleIterator tmp = *this; ++ptr_; return tmp; }
    SimpleIterator& operator--() { --ptr_; return *this; }
    SimpleIterator operator--(int) { SimpleIterator tmp = *this; --ptr_; return tmp; }
    SimpleIterator& operator+=(difference_type n) { ptr_ += n; return *this; }
    SimpleIterator operator+(difference_type n) const { return SimpleIterator(ptr_ + n); }
    difference_type operator-(const SimpleIterator& other) const { return ptr_ - other.ptr_; }
    bool operator==(const SimpleIterator& other) const { return ptr_ == other.ptr_; }
    bool operator!=(const SimpleIterator& other) const { return ptr_ != other.ptr_; }
};

// 使用迭代器 traits
template<typename Iter>
void analyze_iterator() {
    using traits = std::iterator_traits<Iter>;
    
    std::cout << "Iterator analysis:" << std::endl;
    std::cout << "  value_type size: " << sizeof(typename traits::value_type) << std::endl;
    std::cout << "  is random access: " 
              << std::is_same_v<typename traits::iterator_category, 
                               std::random_access_iterator_tag> << std::endl;
}

int main() {
    std::vector<int> vec = {1, 2, 3};
    std::list<int> lst = {4, 5, 6};
    
    analyze_iterator<std::vector<int>::iterator>();
    analyze_iterator<std::list<int>::iterator>();
    
    int arr[] = {7, 8, 9};
    SimpleIterator<int> it(arr);
    std::cout << "Custom iterator value: " << *it << std::endl;  // 7
    ++it;
    std::cout << "After increment: " << *it << std::endl;  // 8
    
    return 0;
}
```

## 10. 值类别 (Value Categories)

**标准版本**: C++11 重新定义

**详细讲解**:
C++11 引入了新的值类别系统：glvalue（泛左值）、prvalue（纯右值）、xvalue（将亡值）、lvalue（左值）、rvalue（右值）。这是理解移动语义和完美转发的基础。主要分类是：表达式要么是 glvalue 要么是 rvalue，glvalue 包括 lvalue 和 xvalue，rvalue 包括 prvalue 和 xvalue。

**演示代码**:
```cpp
#include <iostream>
#include <type_traits>

struct S {
    int value;
    S(int v) : value(v) { std::cout << "Construct " << value << std::endl; }
    ~S() { std::cout << "Destruct " << value << std::endl; }
};

S make_s(int v) {
    return S(v);  // prvalue
}

int main() {
    // lvalue: 有名字的对象
    int x = 10;
    int& lref = x;  // lvalue reference
    
    // prvalue: 临时对象、字面量
    int y = 20;  // 20 是 prvalue
    
    // xvalue: 将亡值，std::move 的结果
    int&& rref = std::move(x);  // std::move(x) 是 xvalue
    
    // 类型推导
    auto a = x;           // a 是 int (lvalue -> 拷贝)
    auto&& b = x;         // b 是 int& (转发引用，绑定到 lvalue)
    auto&& c = 10;        // c 是 int&& (转发引用，绑定到 rvalue)
    auto&& d = std::move(x);  // d 是 int&& (绑定到 xvalue)
    
    // 值类别影响对象生命期
    S s1(1);              // lvalue
    S s2 = make_s(2);     // prvalue，可能触发拷贝省略
    S s3 = std::move(s1); // xvalue，触发移动构造
    
    // decltype 保留值类别
    decltype(x) var1 = x;           // int
    decltype((x)) var2 = x;         // int& (表达式是lvalue)
    decltype(std::move(x)) var3 = std::move(y);  // int&&
    
    std::cout << "is_lvalue_reference var2: " 
              << std::is_lvalue_reference_v<decltype(var2)> << std::endl;
    
    return 0;
}
```

## 11. 左值引用和右值引用

**标准版本**: 左值引用 C++98，右值引用 C++11

**详细讲解**:
左值引用（`T&`）绑定到左值，右值引用（`T&&`）绑定到右值。右值引用是C++11引入的，用于支持移动语义，避免不必要的拷贝。注意函数模板中的 `T&&` 是转发引用，不是普通右值引用。

**演示代码**:
```cpp
#include <iostream>
#include <utility>

class Buffer {
    int* data_;
    size_t size_;
public:
    // 构造函数
    Buffer(size_t size) : size_(size), data_(new int[size]) {
        std::cout << "Constructor, size=" << size_ << std::endl;
    }
    
    // 拷贝构造（左值引用）
    Buffer(const Buffer& other) : size_(other.size_), data_(new int[size_]) {
        std::copy(other.data_, other.data_ + size_, data_);
        std::cout << "Copy constructor, size=" << size_ << std::endl;
    }
    
    // 移动构造（右值引用）
    Buffer(Buffer&& other) noexcept : size_(other.size_), data_(other.data_) {
        other.data_ = nullptr;
        other.size_ = 0;
        std::cout << "Move constructor, size=" << size_ << std::endl;
    }
    
    // 拷贝赋值
    Buffer& operator=(const Buffer& other) {
        if (this != &other) {
            delete[] data_;
            size_ = other.size_;
            data_ = new int[size_];
            std::copy(other.data_, other.data_ + size_, data_);
            std::cout << "Copy assignment" << std::endl;
        }
        return *this;
    }
    
    // 移动赋值
    Buffer& operator=(Buffer&& other) noexcept {
        if (this != &other) {
            delete[] data_;
            data_ = other.data_;
            size_ = other.size_;
            other.data_ = nullptr;
            other.size_ = 0;
            std::cout << "Move assignment" << std::endl;
        }
        return *this;
    }
    
    ~Buffer() {
        delete[] data_;
        std::cout << "Destructor" << std::endl;
    }
};

Buffer create_buffer() {
    return Buffer(100);  // 返回临时对象（prvalue）
}

int main() {
    Buffer b1(50);              // Constructor
    Buffer b2 = b1;             // Copy constructor (左值)
    Buffer b3 = std::move(b1);  // Move constructor (xvalue)
    Buffer b4 = create_buffer(); // Move constructor (prvalue, 或拷贝省略)
    
    b2 = b3;                    // Copy assignment
    b2 = std::move(b3);         // Move assignment
    
    // 引用类型
    int x = 10;
    int& lref = x;              // 左值引用
    // int& lref2 = 10;         // 错误：不能绑定到右值
    const int& clref = 10;      // const 左值引用可以绑定到右值
    
    int&& rref = 10;            // 右值引用
    // int&& rref2 = x;         // 错误：不能绑定到左值
    int&& rref3 = std::move(x); // 可以绑定到 xvalue
    
    return 0;
}
```

## 12. 泛左值 (glvalue)、纯右值 (prvalue)

**标准版本**: C++11

**详细讲解**:
- **glvalue** (generalized lvalue): 泛左值，包括 lvalue 和 xvalue，特点是可以取地址或确定对象身份
- **prvalue** (pure rvalue): 纯右值，用于初始化对象的临时值，包括字面量、返回非引用类型的函数调用等
- **xvalue** (expiring value): 将亡值，生命周期即将结束但资源可以被移动的对象，如 `std::move` 的结果

**演示代码**:
```cpp
#include <iostream>
#include <type_traits>
#include <vector>

struct X {
    int value;
    X(int v) : value(v) { std::cout << "X(" << v << ")" << std::endl; }
    ~X() { std::cout << "~X(" << value << ")" << std::endl; }
};

X create_x() {
    return X(42);  // prvalue
}

int main() {
    // lvalue 示例
    X x1(1);           // x1 是 lvalue
    X& ref = x1;       // 绑定到 lvalue
    X* ptr = &x1;      // 可以取地址
    
    // prvalue 示例
    X x2 = X(2);       // X(2) 是 prvalue，可能触发拷贝省略
    X x3 = create_x(); // create_x() 返回 prvalue
    // &X(3);          // 错误：不能对 prvalue 取地址
    
    // xvalue 示例
    X x4(4);
    X x5 = std::move(x4);  // std::move(x4) 是 xvalue
    
    // glvalue 包括 lvalue 和 xvalue
    // 可以通过 decltype 区分
    std::cout << "\nType analysis:" << std::endl;
    std::cout << "x1 is lvalue ref: " 
              << std::is_lvalue_reference_v<decltype((x1))> << std::endl;
    std::cout << "std::move(x1) is rvalue ref: " 
              << std::is_rvalue_reference_v<decltype(std::move(x1))> << std::endl;
    
    // prvalue 的临时量实质化（C++17）
    const X& cref = X(5);  // prvalue 实质化为临时对象，生命期延长
    
    std::cout << "\nEnd of main" << std::endl;
    return 0;
}
```

## 13. 移动语义 (Move Semantics)

**标准版本**: C++11

**详细讲解**:
移动语义允许资源从一个对象转移到另一个对象，而不是拷贝。通过右值引用和移动构造函数/移动赋值运算符实现。`std::move` 将左值转换为右值引用（实际是条件性转换为 xvalue），允许移动而非拷贝。这是现代C++性能优化的核心特性。

**演示代码**:
```cpp
#include <iostream>
#include <vector>
#include <string>
#include <algorithm>

class String {
    char* data_;
    size_t size_;
    
public:
    // 构造函数
    String(const char* str = "") {
        size_ = std::strlen(str);
        data_ = new char[size_ + 1];
        std::strcpy(data_, str);
        std::cout << "Construct: " << data_ << std::endl;
    }
    
    // 拷贝构造 - 深拷贝
    String(const String& other) : size_(other.size_) {
        data_ = new char[size_ + 1];
        std::strcpy(data_, other.data_);
        std::cout << "Copy: " << data_ << std::endl;
    }
    
    // 移动构造 - 资源转移
    String(String&& other) noexcept : data_(other.data_), size_(other.size_) {
        other.data_ = nullptr;
        other.size_ = 0;
        std::cout << "Move: " << data_ << std::endl;
    }
    
    // 拷贝赋值
    String& operator=(const String& other) {
        if (this != &other) {
            delete[] data_;
            size_ = other.size_;
            data_ = new char[size_ + 1];
            std::strcpy(data_, other.data_);
            std::cout << "Copy assign: " << data_ << std::endl;
        }
        return *this;
    }
    
    // 移动赋值
    String& operator=(String&& other) noexcept {
        if (this != &other) {
            delete[] data_;
            data_ = other.data_;
            size_ = other.size_;
            other.data_ = nullptr;
            other.size_ = 0;
            std::cout << "Move assign: " << data_ << std::endl;
        }
        return *this;
    }
    
    ~String() {
        if (data_) std::cout << "Destruct: " << data_ << std::endl;
        delete[] data_;
    }
    
    const char* c_str() const { return data_; }
};

String create_string(const char* s) {
    return String(s);  // 返回临时对象
}

int main() {
    std::vector<String> vec;
    
    String s1("Hello");
    vec.push_back(s1);              // 拷贝
    vec.push_back(std::move(s1));   // 移动（s1 之后不应再使用）
    vec.push_back(create_string("World"));  // 移动（或拷贝省略）
    
    std::cout << "\n--- Using std::move with standard containers ---\n";
    std::vector<int> v1 = {1, 2, 3, 4, 5};
    std::vector<int> v2 = std::move(v1);  // v1 的资源转移到 v2
    std::cout << "v1 size after move: " << v1.size() << std::endl;  // 0
    std::cout << "v2 size: " << v2.size() << std::endl;  // 5
    
    return 0;
}
```

## 14. 转发引用 (Forwarding Reference) / 万能引用

**标准版本**: C++11

**详细讲解**:
转发引用（也称万能引用）是函数模板参数中的 `T&&` 形式，它可以绑定到任何值类别。通过引用折叠规则，`T&&` 既可以是左值引用也可以是右值引用。这是实现完美转发的基础。注意：只有在类型推导上下文中的 `T&&` 才是转发引用。

**演示代码**:
```cpp
#include <iostream>
#include <utility>
#include <type_traits>

// 转发引用示例
template<typename T>
void process(T&& arg) {  // T&& 是转发引用
    std::cout << "Received: ";
    if constexpr (std::is_lvalue_reference_v<T>) {
        std::cout << "lvalue" << std::endl;
    } else {
        std::cout << "rvalue" << std::endl;
    }
}

// 引用折叠规则演示
void demonstrate_reference_collapsing() {
    int x = 10;
    
    // 引用折叠规则：
    // T& & -> T&
    // T& && -> T&
    // T&& & -> T&
    // T&& && -> T&&
    
    using LRef = int&;
    using RRef = int&&;
    
    using Type1 = LRef&;    // int& & -> int&
    using Type2 = LRef&&;   // int& && -> int&
    using Type3 = RRef&;    // int&& & -> int&
    using Type4 = RRef&&;   // int&& && -> int&&
    
    std::cout << "Type1 is lvalue ref: " 
              << std::is_lvalue_reference_v<Type1> << std::endl;  // 1
    std::cout << "Type4 is rvalue ref: " 
              << std::is_rvalue_reference_v<Type4> << std::endl;  // 1
}

// 区分转发引用和普通右值引用
template<typename T>
void f1(T&& param) {  // 转发引用（在类型推导上下文）
    std::cout << "Forwarding reference" << std::endl;
}

template<typename T>
class Widget {
public:
    void f2(T&& param) {  // 普通右值引用（无类型推导）
        std::cout << "Rvalue reference" << std::endl;
    }
    
    template<typename U>
    void f3(U&& param) {  // 转发引用（有类型推导）
        std::cout << "Forwarding reference in member" << std::endl;
    }
};

int main() {
    int x = 10;
    const int cx = 20;
    
    process(x);             // T 推导为 int&
    process(cx);            // T 推导为 const int&
    process(10);            // T 推导为 int
    process(std::move(x));  // T 推导为 int
    
    demonstrate_reference_collapsing();
    
    f1(x);          // 转发引用可以绑定到左值
    f1(10);         // 转发引用可以绑定到右值
    
    Widget<int> w;
    // w.f2(x);     // 错误：右值引用不能绑定到左值
    w.f2(10);       // 正确
    w.f3(x);        // 转发引用可以绑定
    
    return 0;
}
```

## 15. std::forward 完美转发

**标准版本**: C++11

**详细讲解**:
`std::forward<T>()` 用于在函数模板中保持参数的值类别，将左值转发为左值，将右值转发为右值。这使得包装函数能够精确地将参数传递给内部函数，保持移动语义。完美转发是实现通用包装器和工厂函数的关键技术。

**演示代码**:
```cpp
#include <iostream>
#include <utility>
#include <memory>

void process_value(int& x) {
    std::cout << "lvalue: " << x << std::endl;
}

void process_value(int&& x) {
    std::cout << "rvalue: " << x << std::endl;
}

// 不使用完美转发的版本（错误示范）
template<typename T>
void bad_wrapper(T&& arg) {
    // arg 本身是一个具名变量，因此是左值
    process_value(arg);  // 总是调用左值版本！
}

// 使用完美转发的正确版本
template<typename T>
void good_wrapper(T&& arg) {
    // 使用 std::forward 保持原始值类别
    process_value(std::forward<T>(arg));
}

// 完美转发在工厂函数中的应用
class MyClass {
    int value_;
    std::string name_;
public:
    MyClass(int v, std::string n) : value_(v), name_(std::move(n)) {
        std::cout << "MyClass(" << value_ << ", " << name_ << ")" << std::endl;
    }
};

template<typename T, typename... Args>
std::unique_ptr<T> make_unique_perfect(Args&&... args) {
    // 完美转发所有参数给 T 的构造函数
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
}

// 多参数完美转发
template<typename F, typename... Args>
void call_with_forward(F&& func, Args&&... args) {
    std::forward<F>(func)(std::forward<Args>(args)...);
}

void multi_param_func(int& a, int&& b, const int& c) {
    std::cout << "a=" << a << ", b=" << b << ", c=" << c << std::endl;
    a = 100;  // 修改左值引用
}

int main() {
    int x = 42;
    
    std::cout << "Bad wrapper:" << std::endl;
    bad_wrapper(x);           // 传入左值
    bad_wrapper(10);          // 传入右值，但仍调用左值版本！
    
    std::cout << "\nGood wrapper:" << std::endl;
    good_wrapper(x);          // 正确调用左值版本
    good_wrapper(10);         // 正确调用右值版本
    good_wrapper(std::move(x)); // 正确调用右值版本
    
    std::cout << "\nFactory with perfect forwarding:" << std::endl;
    std::string name = "Alice";
    auto obj1 = make_unique_perfect<MyClass>(42, name);  // 拷贝 name
    auto obj2 = make_unique_perfect<MyClass>(100, std::move(name));  // 移动 name
    
    std::cout << "\nMulti-parameter forwarding:" << std::endl;
    int a = 1, b = 2, c = 3;
    call_with_forward(multi_param_func, a, std::move(b), c);
    std::cout << "a after call: " << a << std::endl;  // 100
    
    return 0;
}
```

## 16. RAII (Resource Acquisition Is Initialization)

**标准版本**: C++98/03 的核心理念

**详细讲解**:
RAII 是C++资源管理的基本原则：资源的获取即初始化，资源的释放在析构函数中进行。这保证了异常安全性和资源的自动管理。标准库的智能指针、文件流、互斥锁等都是 RAII 的典型应用。

**演示代码**:
```cpp
#include <iostream>
#include <memory>
#include <fstream>
#include <mutex>

// 手动实现 RAII 包装器
class FileHandle {
    FILE* file_;
public:
    FileHandle(const char* filename, const char* mode) {
        file_ = fopen(filename, mode);
        if (!file_) {
            throw std::runtime_error("Failed to open file");
        }
        std::cout << "File opened" << std::endl;
    }
    
    ~FileHandle() {
        if (file_) {
            fclose(file_);
            std::cout << "File closed" << std::endl;
        }
    }
    
    // 禁止拷贝
    FileHandle(const FileHandle&) = delete;
    FileHandle& operator=(const FileHandle&) = delete;
    
    // 允许移动
    FileHandle(FileHandle&& other) noexcept : file_(other.file_) {
        other.file_ = nullptr;
    }
    
    FILE* get() const { return file_; }
};

// 互斥锁的 RAII 包装
class MutexLock {
    std::mutex& mutex_;
public:
    explicit MutexLock(std::mutex& m) : mutex_(m) {
        mutex_.lock();
        std::cout << "Mutex locked" << std::endl;
    }
    
    ~MutexLock() {
        mutex_.unlock();
        std::cout << "Mutex unlocked" << std::endl;
    }
    
    MutexLock(const MutexLock&) = delete;
    MutexLock& operator=(const MutexLock&) = delete;
};

// 自定义资源的 RAII
class Connection {
    int id_;
    bool connected_;
public:
    Connection(int id) : id_(id), connected_(true) {
        std::cout << "Connection " << id_ << " established" << std::endl;
    }
    
    ~Connection() {
        if (connected_) {
            disconnect();
        }
    }
    
    void disconnect() {
        if (connected_) {
            std::cout << "Connection " << id_ << " closed" << std::endl;
            connected_ = false;
        }
    }
    
    Connection(const Connection&) = delete;
    Connection& operator=(const Connection&) = delete;
};

void demonstrate_raii() {
    // 智能指针 RAII
    {
        std::unique_ptr<int> ptr(new int(42));
        std::cout << "Unique ptr value: " << *ptr << std::endl;
        // ptr 自动释放
    }
    
    // 文件流 RAII
    {
        std::ofstream file("test.txt");
        file << "Hello RAII" << std::endl;
        // file 自动关闭
    }
    
    // 自定义 RAII
    {
        Connection conn(1);
        // 使用连接...
        // 即使发生异常，析构函数也会调用
    }
}

int main() {
    try {
        demonstrate_raii();
        
        // 即使抛出异常，RAII 对象也会正确析构
        std::unique_ptr<int> ptr(new int(100));
        // throw std::runtime_error("Something went wrong");
        
    } catch (const std::exception& e) {
        std::cout << "Exception: " << e.what() << std::endl;
    }
    
    return 0;
}
```

## 17. 表达式求值、弃值表达式、不求值表达式

**标准版本**: C++98/03，C++11 增强

**详细讲解**:
- **表达式求值**：计算表达式的值和副作用
- **弃值表达式**：只关心副作用，不关心返回值的表达式（如语句表达式）
- **不求值表达式**：只用于编译期类型推导，不实际执行的表达式，如 `sizeof`、`decltype`、`typeid`、`noexcept`

**演示代码**:
```cpp
#include <iostream>
#include <type_traits>

int global_counter = 0;

int increment() {
    return ++global_counter;
}

struct S {
    S() { std::cout << "S constructed" << std::endl; }
    ~S() { std::cout << "S destructed" << std::endl; }
    int value() const { return 42; }
};

S create_s() {
    std::cout << "create_s called" << std::endl;
    return S();
}

int main() {
    // 正常求值表达式
    std::cout << "Normal evaluation:" << std::endl;
    int x = increment();  // increment() 被求值，global_counter 增加
    std::cout << "x = " << x << ", counter = " << global_counter << std::endl;
    
    // 弃值表达式 - 只执行副作用
    std::cout << "\nDiscarded-value expression:" << std::endl;
    increment();  // 返回值被丢弃，但副作用（++global_counter）发生
    std::cout << "counter = " << global_counter << std::endl;
    
    // 不求值表达式 - sizeof
    std::cout << "\nUnevaluated expression - sizeof:" << std::endl;
    size_t size = sizeof(increment());  // increment() 不被调用
    std::cout << "Size: " << size << ", counter: " << global_counter << std::endl;
    
    // 不求值表达式 - decltype
    std::cout << "\nUnevaluated expression - decltype:" << std::endl;
    decltype(create_s()) s_type;  // create_s() 不被调用，没有构造
    std::cout << "After decltype" << std::endl;
    
    // 不求值表达式 - typeid
    std::cout << "\nUnevaluated expression - typeid:" << std::endl;
    std::cout << "Type: " << typeid(increment()).name() << std::endl;
    std::cout << "counter: " << global_counter << std::endl;
    
    // decltype(auto) 推导
    S s;
    decltype(auto) ref = (s);  // decltype((s)) 是 S&
    decltype(auto) val = s.value();  // decltype(s.value()) 是 int
    
    // noexcept 也是不求值的
    bool is_noexcept = noexcept(increment());
    std::cout << "\nincrement is noexcept: " << is_noexcept << std::endl;
    std::cout << "counter: " << global_counter << std::endl;
    
    return 0;
}
```

## 18. 潜在求值表达式、常量表达式

**标准版本**: C++11 引入 constexpr，C++14/17/20 增强

**详细讲解**:
- **潜在求值表达式**：在运行时可能被求值的表达式
- **常量表达式**：能在编译期求值的表达式，用 `constexpr` 标记。C++11 引入，C++14 放宽限制，C++17 引入 `if constexpr`，C++20 大幅扩展

**演示代码**:
```cpp
#include <iostream>
#include <array>

// constexpr 函数（编译期可求值）
constexpr int factorial(int n) {
    return (n <= 1) ? 1 : n * factorial(n - 1);
}

// C++14 constexpr 可以有多个语句
constexpr int fibonacci(int n) {
    if (n <= 1) return n;
    int a = 0, b = 1;
    for (int i = 2; i <= n; ++i) {
        int tmp = a + b;
        a = b;
        b = tmp;
    }
    return b;
}

// constexpr 类
class Point {
    int x_, y_;
public:
    constexpr Point(int x, int y) : x_(x), y_(y) {}
    constexpr int x() const { return x_; }
    constexpr int y() const { return y_; }
    constexpr int distance_squared() const { return x_*x_ + y_*y_; }
};

// C++17 if constexpr
template<typename T>
constexpr auto get_value(T t) {
    if constexpr (std::is_pointer_v<T>) {
        return *t;  // 如果是指针，解引用
    } else {
        return t;   // 否则直接返回
    }
}

// constexpr 变量
constexpr int max_size = 100;
constexpr Point origin(0, 0);

int main() {
    // 编译期常量
    constexpr int fact5 = factorial(5);  // 编译期计算
    std::cout << "5! = " << fact5 << std::endl;
    
    // 用于数组大小
    int arr[factorial(4)];  // 数组大小必须是常量表达式
    std::cout << "Array size: " << sizeof(arr) / sizeof(int) << std::endl;
    
    // constexpr 对象
    constexpr Point p(3, 4);
    constexpr int dist = p.distance_squared();  // 编译期计算
    std::cout << "Distance squared: " << dist << std::endl;
    
    // 运行时使用
    int n;
    std::cin >> n;
    int fib_n = fibonacci(n);  // 运行时计算（也可以编译期）
    std::cout << "Fibonacci(" << n << ") = " << fib_n << std::endl;
    
    // if constexpr 示例
    int value = 10;
    int* ptr = &value;
    std::cout << "get_value(value): " << get_value(value) << std::endl;
    std::cout << "get_value(ptr): " << get_value(ptr) << std::endl;
    
    // C++20 consteval（立即函数，必须在编译期求值）
    // consteval int square(int n) { return n * n; }
    // constexpr int s = square(5);  // OK
    // int x = 5; square(x);  // 错误，x 不是常量
    
    return 0;
}
```

## 19. 临时量实质化 (Temporary Materialization)

**标准版本**: C++17

**详细讲解**:
临时量实质化是C++17引入的概念，将纯右值（prvalue）转换为临时对象（xvalue）的过程。这发生在需要 glvalue 的地方，如绑定到引用、访问成员等。C++17 强制拷贝消除也与此相关。

**演示代码**:
```cpp
#include <iostream>

struct S {
    int value;
    S(int v) : value(v) { 
        std::cout << "S(" << value << ") constructed at " << this << std::endl; 
    }
    ~S() { 
        std::cout << "S(" << value << ") destructed at " << this << std::endl; 
    }
    S(const S& other) : value(other.value) {
        std::cout << "S copy constructed from " << &other << " to " << this << std::endl;
    }
};

S create_s(int v) {
    return S(v);  // prvalue
}

struct T {
    int x;
    int y;
};

T create_t() {
    return {1, 2};  // prvalue
}

int main() {
    std::cout << "=== Temporary materialization scenarios ===" << std::endl;
    
    // 1. 绑定到 const 左值引用触发实质化
    std::cout << "\n1. Binding to const lvalue reference:" << std::endl;
    const S& ref = create_s(1);  // create_s() 返回 prvalue，实质化为临时对象
    std::cout << "ref bound to address: " << &ref << std::endl;
    // 临时对象生命期延长到 ref 的作用域结束
    
    // 2. 绑定到右值引用触发实质化
    std::cout << "\n2. Binding to rvalue reference:" << std::endl;
    S&& rref = create_s(2);
    std::cout << "rref bound to address: " << &rref << std::endl;
    
    // 3. 访问成员触发实质化
    std::cout << "\n3. Member access:" << std::endl;
    int x_value = create_t().x;  // create_t() 返回 prvalue，访问 .x 触发实质化
    std::cout << "x_value: " << x_value << std::endl;
    
    // 4. 数组下标触发实质化
    std::cout << "\n4. Array subscript:" << std::endl;
    struct Array { int data[3]; };
    auto get_array = []() { return Array{{1, 2, 3}}; };
    int element = get_array()[1];  // 实质化后访问数组元素
    std::cout << "element: " << element << std::endl;
    
    // 5. C++17 保证的拷贝消除
    std::cout << "\n5. Guaranteed copy elision (C++17):" << std::endl;
    S s = create_s(3);  // C++17: 不发生拷贝，直接在 s 的位置构造
    // 在 C++17 之前可能会有临时对象的拷贝
    
    // 6. 不实质化的情况：直接初始化
    std::cout << "\n6. Direct initialization without materialization:" << std::endl;
    S s2(create_s(4));  // C++17: 直接在 s2 位置构造，无临时对象
    
    std::cout << "\n=== End of scope ===" << std::endl;
    return 0;
}
```

## 20. 标准布局类 (Standard Layout Class)

**标准版本**: C++11

**详细讲解**:
标准布局类是满足特定布局要求的类，可以安全地与C代码交互。要求包括：所有非静态数据成员有相同的访问控制、没有虚函数、没有虚基类、所有非静态数据成员都是标准布局类型等。可用 `std::is_standard_layout` 检查。

**演示代码**:
```cpp
#include <iostream>
#include <type_traits>

// 标准布局类
struct StandardLayout {
    int x;
    double y;
    char z;
    
    void method() {}  // 成员函数不影响标准布局
    static int static_var;  // 静态成员不影响标准布局
};

// 非标准布局：有虚函数
struct NonStandardVirtual {
    int x;
    virtual void func() {}
};

// 非标准布局：不同访问控制
struct NonStandardAccess {
    int public_x;
private:
    int private_y;
public:
    int another_public;
};

// 非标准布局：有非标准布局的基类和成员
struct Base {
    int base_x;
};

struct NonStandardInheritance : Base {
    int derived_x;  // 基类和派生类都有非静态成员
};

// 标准布局的继承（只有一个类有非静态成员）
struct StandardLayoutBase {
    void method() {}
};

struct StandardLayoutDerived : StandardLayoutBase {
    int x;
    double y;
};

// POD (Plain Old Data) 类型
// POD = 标准布局 + 平凡类型
struct POD {
    int x;
    double y;
};

// 与C代码交互的示例
extern "C" {
    struct CStruct {
        int x;
        double y;
        char z;
    };
    
    void c_function(CStruct* s);  // 假设这是C函数
}

int main() {
    std::cout << "=== Standard Layout Type Checks ===" << std::endl;
    
    std::cout << "StandardLayout is standard layout: " 
              << std::is_standard_layout_v<StandardLayout> << std::endl;  // 1
    
    std::cout << "NonStandardVirtual is standard layout: " 
              << std::is_standard_layout_v<NonStandardVirtual> << std::endl;  // 0
    
    std::cout << "NonStandardAccess is standard layout: " 
              << std::is_standard_layout_v<NonStandardAccess> << std::endl;  // 0
    
    std::cout << "NonStandardInheritance is standard layout: " 
              << std::is_standard_layout_v<NonStandardInheritance> << std::endl;  // 0
    
    std::cout << "StandardLayoutDerived is standard layout: " 
              << std::is_standard_layout_v<StandardLayoutDerived> << std::endl;  // 1
    
    std::cout << "\n=== POD Type Checks ===" << std::endl;
    std::cout << "POD is standard layout: " 
              << std::is_standard_layout_v<POD> << std::endl;  // 1
    std::cout << "POD is trivial: " 
              << std::is_trivial_v<POD> << std::endl;  // 1
    std::cout << "POD is POD: " 
              << std::is_pod_v<POD> << std::endl;  // 1 (C++20废弃)
    
    // 与C代码交互
    StandardLayout sl{1, 2.5, 'a'};
    // 可以安全地将标准布局类型转换为C结构体
    // c_function(reinterpret_cast<CStruct*>(&sl));
    
    // offsetof 只能用于标准布局类型
    std::cout << "\n=== offsetof usage ===" << std::endl;
    std::cout << "Offset of x: " << offsetof(StandardLayout, x) << std::endl;
    std::cout << "Offset of y: " << offsetof(StandardLayout, y) << std::endl;
    std::cout << "Offset of z: " << offsetof(StandardLayout, z) << std::endl;
    
    return 0;
}
```

## 21. 元编程实现 constexpr 编译期算法

**标准版本**: C++11 引入 constexpr，C++14/17/20 增强

**详细讲解**:
模板元编程允许在编译期执行计算。C++11的constexpr提供了更直观的方式。这里展示编译期递归、汉诺塔、字符串处理和函数表生成。

**演示代码**:
```cpp
#include <iostream>
#include <array>

// 1. 编译期汉诺塔
constexpr int hanoi_moves(int n) {
    return (n == 1) ? 1 : 2 * hanoi_moves(n - 1) + 1;
}

// 2. 编译期斐波那契（模板元编程方式）
template<int N>
struct Fibonacci {
    static constexpr int value = Fibonacci<N-1>::value + Fibonacci<N-2>::value;
};

template<>
struct Fibonacci<0> {
    static constexpr int value = 0;
};

template<>
struct Fibonacci<1> {
    static constexpr int value = 1;
};

// 3. 编译期字符串长度
constexpr std::size_t const_strlen(const char* str) {
    return *str ? 1 + const_strlen(str + 1) : 0;
}

// 4. 编译期字符串拼接
template<std::size_t N1, std::size_t N2>
constexpr auto concat_strings(const char (&s1)[N1], const char (&s2)[N2]) {
    std::array<char, N1 + N2 - 1> result{};
    
    for (std::size_t i = 0; i < N1 - 1; ++i) {
        result[i] = s1[i];
    }
    for (std::size_t i = 0; i < N2; ++i) {
        result[N1 - 1 + i] = s2[i];
    }
    
    return result;
}

// 5. 编译期函数表
template<typename T, std::size_t N>
struct FunctionTable {
    using FuncType = T(*)(T);
    std::array<FuncType, N> functions;
    
    constexpr FunctionTable() : functions{} {
        for (std::size_t i = 0; i < N; ++i) {
            functions[i] = nullptr;
        }
    }
    
    constexpr void set(std::size_t idx, FuncType func) {
        functions[idx] = func;
    }
    
    constexpr FuncType get(std::size_t idx) const {
        return functions[idx];
    }
};

constexpr int square(int x) { return x * x; }
constexpr int cube(int x) { return x * x * x; }
constexpr int double_value(int x) { return x * 2; }

constexpr auto create_function_table() {
    FunctionTable<int, 3> table;
    table.set(0, square);
    table.set(1, cube);
    table.set(2, double_value);
    return table;
}

// 6. 编译期质数检查
constexpr bool is_prime(int n, int divisor = 2) {
    return (n <= 1) ? false :
           (divisor * divisor > n) ? true :
           (n % divisor == 0) ? false :
           is_prime(n, divisor + 1);
}

// 7. 编译期生成质数表
template<std::size_t N>
constexpr auto generate_primes() {
    std::array<int, N> primes{};
    std::size_t count = 0;
    int candidate = 2;
    
    while (count < N) {
        if (is_prime(candidate)) {
            primes[count++] = candidate;
        }
        ++candidate;
    }
    
    return primes;
}

int main() {
    // 编译期汉诺塔
    constexpr int moves_5 = hanoi_moves(5);
    std::cout << "Hanoi moves for 5 disks: " << moves_5 << std::endl;
    
    // 编译期斐波那契
    constexpr int fib_10 = Fibonacci<10>::value;
    std::cout << "Fibonacci(10): " << fib_10 << std::endl;
    
    // 编译期字符串长度
    constexpr std::size_t len = const_strlen("Hello");
    std::cout << "String length: " << len << std::endl;
    
    // 编译期字符串拼接
    constexpr auto result = concat_strings("Hello, ", "World!");
    std::cout << "Concatenated: " << result.data() << std::endl;
    
    // 编译期函数表
    constexpr auto func_table = create_function_table();
    std::cout << "Function table[0](5) = " << func_table.get(0)(5) << std::endl;
    std::cout << "Function table[1](5) = " << func_table.get(1)(5) << std::endl;
    std::cout << "Function table[2](5) = " << func_table.get(2)(5) << std::endl;
    
    // 编译期质数
    constexpr bool is_17_prime = is_prime(17);
    std::cout << "17 is prime: " << is_17_prime << std::endl;
    
    // 编译期质数表
    constexpr auto primes = generate_primes<10>();
    std::cout << "First 10 primes: ";
    for (auto p : primes) {
        std::cout << p << " ";
    }
    std::cout << std::endl;
    
    return 0;
}
```

## 22. 用户定义字面量 (User-Defined Literals)

**标准版本**: C++11

**详细讲解**:
用户定义字面量允许为自定义类型创建字面量后缀，使代码更具表达力。通过 `operator""` 定义。标准库已提供如 `s`（string）、`ms`（milliseconds）等字面量。

**演示代码**:
```cpp
#include <iostream>
#include <string>
#include <complex>
#include <chrono>

// 1. 距离单位
class Distance {
    double meters_;
public:
    explicit Distance(double m) : meters_(m) {}
    double meters() const { return meters_; }
    double kilometers() const { return meters_ / 1000.0; }
};

// 定义字面量后缀
constexpr Distance operator"" _m(long double val) {
    return Distance(static_cast<double>(val));
}

constexpr Distance operator"" _km(long double val) {
    return Distance(static_cast<double>(val * 1000));
}

constexpr Distance operator"" _cm(long double val) {
    return Distance(static_cast<double>(val / 100));
}

// 2. 二进制字面量
constexpr unsigned long long operator"" _b(const char* str, std::size_t) {
    unsigned long long result = 0;
    while (*str) {
        result = result * 2 + (*str - '0');
        ++str;
    }
    return result;
}

// 3. 颜色RGB
struct Color {
    unsigned char r, g, b;
    Color(unsigned char red, unsigned char green, unsigned char blue)
        : r(red), g(green), b(blue) {}
};

constexpr Color operator"" _rgb(unsigned long long val) {
    return Color(
        (val >> 16) & 0xFF,
        (val >> 8) & 0xFF,
        val & 0xFF
    );
}

// 4. 温度单位
class Temperature {
    double kelvin_;
public:
    explicit Temperature(double k) : kelvin_(k) {}
    double kelvin() const { return kelvin_; }
    double celsius() const { return kelvin_ - 273.15; }
    double fahrenheit() const { return celsius() * 9.0/5.0 + 32.0; }
};

constexpr Temperature operator"" _K(long double val) {
    return Temperature(static_cast<double>(val));
}

constexpr Temperature operator"" _C(long double val) {
    return Temperature(static_cast<double>(val + 273.15));
}

constexpr Temperature operator"" _F(long double val) {
    return Temperature(static_cast<double>((val - 32.0) * 5.0/9.0 + 273.15));
}

int main() {
    using namespace std::string_literals;  // 启用 s 字面量
    using namespace std::chrono_literals;  // 启用时间字面量
    
    // 标准库字面量
    auto str = "Hello"s;  // std::string
    auto duration = 5s;   // std::chrono::seconds
    auto ms = 100ms;      // std::chrono::milliseconds
    
    std::cout << "String: " << str << std::endl;
    std::cout << "Duration: " << duration.count() << " seconds" << std::endl;
    
    // 自定义距离字面量
    auto d1 = 1.5_km;
    auto d2 = 500_m;
    auto d3 = 50_cm;
    
    std::cout << "\nDistances in meters:" << std::endl;
    std::cout << "1.5km = " << d1.meters() << "m" << std::endl;
    std::cout << "500m = " << d2.meters() << "m" << std::endl;
    std::cout << "50cm = " << d3.meters() << "m" << std::endl;
    
    // 二进制字面量
    auto binary = "1010"_b;
    std::cout << "\nBinary 1010 = " << binary << std::endl;
    
    // 颜色字面量
    auto red = 0xFF0000_rgb;
    auto green = 0x00FF00_rgb;
    std::cout << "\nRed color: R=" << (int)red.r << " G=" << (int)red.g 
              << " B=" << (int)red.b << std::endl;
    
    // 温度字面量
    auto temp1 = 25.0_C;
    auto temp2 = 77.0_F;
    auto temp3 = 300.0_K;
    
    std::cout << "\nTemperatures in Celsius:" << std::endl;
    std::cout << "25°C = " << temp1.celsius() << "°C" << std::endl;
    std::cout << "77°F = " << temp2.celsius() << "°C" << std::endl;
    std::cout << "300K = " << temp3.celsius() << "°C" << std::endl;
    
    return 0;
}
```

## 23. PIMPL (Pointer to Implementation)

**标准版本**: C++98/03 设计模式，C++11 智能指针改进

**详细讲解**:
PIMPL（Pointer to Implementation，指向实现的指针）是一种降低编译依赖的设计模式。将实现细节移到单独的实现类中，在头文件中只保留前向声明和指针。这减少了重新编译的需要，隐藏了实现细节。

**演示代码**:
```cpp
// Widget.h
#ifndef WIDGET_H
#define WIDGET_H

#include <memory>
#include <string>

// 前向声明
class WidgetImpl;

class Widget {
public:
    Widget();
    ~Widget();  // 必须在实现文件中定义，因为需要完整的 WidgetImpl
    
    // 拷贝和移动操作也需要在实现文件中定义
    Widget(const Widget& other);
    Widget& operator=(const Widget& other);
    Widget(Widget&& other) noexcept;
    Widget& operator=(Widget&& other) noexcept;
    
    void set_name(const std::string& name);
    std::string get_name() const;
    void do_something();
    
private:
    std::unique_ptr<WidgetImpl> pImpl;  // PIMPL指针
};

#endif // WIDGET_H

// Widget.cpp
#include <iostream>
#include <vector>

// 实现类定义（只在源文件中）
class WidgetImpl {
public:
    std::string name;
    std::vector<int> data;
    int internal_state;
    
    WidgetImpl() : internal_state(0) {
        std::cout << "WidgetImpl constructed" << std::endl;
    }
    
    ~WidgetImpl() {
        std::cout << "WidgetImpl destructed" << std::endl;
    }
    
    void process() {
        std::cout << "Processing in WidgetImpl..." << std::endl;
        internal_state++;
    }
};

// Widget 实现
Widget::Widget() : pImpl(std::make_unique<WidgetImpl>()) {
    std::cout << "Widget constructed" << std::endl;
}

Widget::~Widget() = default;  // 必须在知道 WidgetImpl 完整定义的地方

Widget::Widget(const Widget& other) 
    : pImpl(std::make_unique<WidgetImpl>(*other.pImpl)) {}

Widget& Widget::operator=(const Widget& other) {
    if (this != &other) {
        *pImpl = *other.pImpl;
    }
    return *this;
}

Widget::Widget(Widget&& other) noexcept = default;
Widget& Widget::operator=(Widget&& other) noexcept = default;

void Widget::set_name(const std::string& name) {
    pImpl->name = name;
}

std::string Widget::get_name() const {
    return pImpl->name;
}

void Widget::do_something() {
    pImpl->process();
}

// main.cpp
int main() {
    Widget w1;
    w1.set_name("Widget 1");
    w1.do_something();
    
    std::cout << "Name: " << w1.get_name() << std::endl;
    
    // 拷贝
    Widget w2 = w1;
    w2.set_name("Widget 2");
    std::cout << "w1: " << w1.get_name() << std::endl;
    std::cout << "w2: " << w2.get_name() << std::endl;
    
    // 移动
    Widget w3 = std::move(w2);
    std::cout << "w3: " << w3.get_name() << std::endl;
    
    return 0;
}

/*
PIMPL 优点：
1. 降低编译依赖：修改实现不需要重新编译使用该类的代码
2. 隐藏实现细节：头文件中不暴露私有成员
3. 减小头文件大小：不需要包含实现所需的头文件
4. 二进制兼容性：修改实现不影响ABI

PIMPL 缺点：
1. 额外的间接层：性能开销（一次指针解引用）
2. 内存开销：额外的指针和动态分配
3. 代码复杂性：需要在源文件中定义特殊成员函数
*/
```

## 24. 三五零原则 (Rule of Three/Five/Zero)

**标准版本**: C++98 三原则，C++11 五原则，C++11 零原则

**详细讲解**:
- **三原则（C++98）**：如果需要自定义析构函数、拷贝构造函数或拷贝赋值运算符之一，通常需要全部定义
- **五原则（C++11）**：添加移动构造函数和移动赋值运算符
- **零原则**：尽量使用RAII和标准库，避免手动管理资源，无需自定义任何特殊成员函数

**演示代码**:
```cpp
#include <iostream>
#include <cstring>
#include <algorithm>

// 1. 违反三原则的错误示例
class BadString {
    char* data_;
public:
    BadString(const char* s) {
        data_ = new char[strlen(s) + 1];
        strcpy(data_, s);
    }
    
    ~BadString() {
        delete[] data_;  // 只定义了析构函数
    }
    // 缺少拷贝构造和拷贝赋值，会导致浅拷贝和双重释放！
};

// 2. 遵循三原则
class GoodStringCpp98 {
    char* data_;
    size_t size_;
    
public:
    // 构造函数
    GoodStringCpp98(const char* s = "") : size_(strlen(s)) {
        data_ = new char[size_ + 1];
        strcpy(data_, s);
    }
    
    // 析构函数
    ~GoodStringCpp98() {
        delete[] data_;
    }
    
    // 拷贝构造函数
    GoodStringCpp98(const GoodStringCpp98& other) : size_(other.size_) {
        data_ = new char[size_ + 1];
        strcpy(data_, other.data_);
        std::cout << "Copy constructor" << std::endl;
    }
    
    // 拷贝赋值运算符
    GoodStringCpp98& operator=(const GoodStringCpp98& other) {
        if (this != &other) {
            // 拷贝-交换惯用法
            GoodStringCpp98 temp(other);
            std::swap(data_, temp.data_);
            std::swap(size_, temp.size_);
            std::cout << "Copy assignment" << std::endl;
        }
        return *this;
    }
    
    const char* c_str() const { return data_; }
};

// 3. 遵循五原则（C++11）
class GoodStringCpp11 {
    char* data_;
    size_t size_;
    
public:
    GoodStringCpp11(const char* s = "") : size_(strlen(s)) {
        data_ = new char[size_ + 1];
        strcpy(data_, s);
    }
    
    ~GoodStringCpp11() {
        delete[] data_;
    }
    
    // 拷贝构造函数
    GoodStringCpp11(const GoodStringCpp11& other) : size_(other.size_) {
        data_ = new char[size_ + 1];
        strcpy(data_, other.data_);
        std::cout << "Copy constructor" << std::endl;
    }
    
    // 拷贝赋值运算符
    GoodStringCpp11& operator=(const GoodStringCpp11& other) {
        if (this != &other) {
            GoodStringCpp11 temp(other);
            std::swap(data_, temp.data_);
            std::swap(size_, temp.size_);
            std::cout << "Copy assignment" << std::endl;
        }
        return *this;
    }
    
    // 移动构造函数
    GoodStringCpp11(GoodStringCpp11&& other) noexcept 
        : data_(other.data_), size_(other.size_) {
        other.data_ = nullptr;
        other.size_ = 0;
        std::cout << "Move constructor" << std::endl;
    }
    
    // 移动赋值运算符
    GoodStringCpp11& operator=(GoodStringCpp11&& other) noexcept {
        if (this != &other) {
            delete[] data_;
            data_ = other.data_;
            size_ = other.size_;
            other.data_ = nullptr;
            other.size_ = 0;
            std::cout << "Move assignment" << std::endl;
        }
        return *this;
    }
    
    const char* c_str() const { return data_; }
};

// 4. 遵循零原则（推荐）
#include <string>
#include <vector>

class BetterString {
    std::string data_;  // 使用标准库管理资源
public:
    BetterString(const char* s = "") : data_(s) {}
    // 无需定义任何特殊成员函数！
    // 编译器自动生成的版本都是正确的
    
    const char* c_str() const { return data_.c_str(); }
};

class DataHolder {
    std::vector<int> data_;
    std::string name_;
public:
    DataHolder(std::string n) : name_(std::move(n)) {}
    // 零原则：无需自定义任何特殊成员函数
};

int main() {
    std::cout << "=== Testing Three/Five Rules ===" << std::endl;
    
    GoodStringCpp11 s1("Hello");
    GoodStringCpp11 s2 = s1;           // 拷贝构造
    GoodStringCpp11 s3("World");
    s3 = s1;                           // 拷贝赋值
    GoodStringCpp11 s4 = std::move(s1); // 移动构造
    s3 = std::move(s2);                // 移动赋值
    
    std::cout << "\n=== Testing Zero Rule ===" << std::endl;
    BetterString bs1("Better");
    BetterString bs2 = bs1;            // 自动正确的拷贝
    BetterString bs3 = std::move(bs1); // 自动正确的移动
    
    return 0;
}

/*
总结：
- 三原则（C++98）：析构函数、拷贝构造、拷贝赋值
- 五原则（C++11）：+ 移动构造、移动赋值
- 零原则（现代C++）：使用RAII类，让编译器自动生成
- 最佳实践：优先使用零原则，必要时才手动管理资源
*/
```

## 25. 构造函数异常处理、函数 try 块

**标准版本**: C++98/03

**详细讲解**:
函数 try 块允许在函数级别捕获异常，特别适用于构造函数的初始化列表。构造函数抛出异常时，已构造的基类和成员会自动析构，但当前对象的析构函数不会被调用。构造函数的函数 try 块主要用于捕获初始化列表中的异常。

**演示代码**:
```cpp
#include <iostream>
#include <stdexcept>
#include <memory>

// 辅助类，用于演示
class Member {
    int value_;
public:
    Member(int v) : value_(v) {
        std::cout << "Member(" << value_ << ") constructed" << std::endl;
        if (value_ < 0) {
            throw std::invalid_argument("Negative value");
        }
    }
    
    ~Member() {
        std::cout << "Member(" << value_ << ") destructed" << std::endl;
    }
    
    int value() const { return value_; }
};

class Base {
public:
    Base(int x) {
        std::cout << "Base constructed with " << x << std::endl;
        if (x == 0) {
            throw std::invalid_argument("Zero not allowed in Base");
        }
    }
    
    ~Base() {
        std::cout << "Base destructed" << std::endl;
    }
};

// 1. 普通异常处理（不推荐在初始化列表抛异常的情况）
class NormalClass : public Base {
    Member m1_;
    Member m2_;
    
public:
    NormalClass(int base_val, int m1_val, int m2_val)
        : Base(base_val), m1_(m1_val), m2_(m2_val) {
        std::cout << "NormalClass constructor body" << std::endl;
        // 如果这里抛异常，m1_ 和 m2_ 会被正确析构
    }
    
    ~NormalClass() {
        std::cout << "NormalClass destructed" << std::endl;
    }
};

// 2. 使用函数 try 块处理初始化列表异常
class FunctionTryClass : public Base {
    Member m1_;
    Member m2_;
    
public:
    FunctionTryClass(int base_val, int m1_val, int m2_val)
    try : Base(base_val), m1_(m1_val), m2_(m2_val) {
        // 构造函数体
        std::cout << "FunctionTryClass constructor body" << std::endl;
    }
    catch (const std::exception& e) {
        // 捕获初始化列表中的异常
        std::cout << "Exception in initialization: " << e.what() << std::endl;
        
        // 注意：此时 m1_, m2_ 等已成功构造的成员会自动析构
        // 但基类如果构造失败则不会析构
        
        // 在构造函数的 catch 块中，异常会自动重新抛出
        // 如果不想重新抛出，需要显式 throw 其他异常
        
        // throw;  // 重新抛出原异常（默认行为）
        throw std::runtime_error("Failed to construct FunctionTryClass");
    }
    
    ~FunctionTryClass() {
        std::cout << "FunctionTryClass destructed" << std::endl;
    }
};

// 3. 函数 try 块用于普通函数
void regular_function(int value)
try {
    std::cout << "Function body with value: " << value << std::endl;
    if (value < 0) {
        throw std::invalid_argument("Negative value");
    }
}
catch (const std::exception& e) {
    std::cout << "Caught in function try block: " << e.what() << std::endl;
    // 对于非构造函数，异常不会自动重新抛出
    // throw;  // 需要显式重新抛出
}

// 4. 析构函数的异常处理（应避免抛异常）
class SafeDestructor {
    std::unique_ptr<int> ptr_;
public:
    SafeDestructor(int val) : ptr_(std::make_unique<int>(val)) {}
    
    ~SafeDestructor() noexcept {  // 析构函数应该是 noexcept
        try {
            // 清理代码
            if (ptr_ && *ptr_ < 0) {
                // 某些可能抛异常的操作
                std::cout << "Cleanup operation" << std::endl;
            }
        }
        catch (...) {
            // 捕获所有异常，不让其逃逸
            std::cout << "Exception caught in destructor" << std::endl;
            // 不要重新抛出！
        }
    }
};

int main() {
    std::cout << "=== Test 1: Normal construction ===" << std::endl;
    try {
        NormalClass nc(1, 2, 3);
    }
    catch (const std::exception& e) {
        std::cout << "Caught: " << e.what() << std::endl;
    }
    
    std::cout << "\n=== Test 2: Exception in member initialization ===" << std::endl;
    try {
        NormalClass nc(1, -1, 3);  // m1_ 构造会抛异常
    }
    catch (const std::exception& e) {
        std::cout << "Caught: " << e.what() << std::endl;
    }
    
    std::cout << "\n=== Test 3: Function try block ===" << std::endl;
    try {
        FunctionTryClass ftc(1, -1, 3);  // m1_ 构造会抛异常
    }
    catch (const std::exception& e) {
        std::cout << "Final catch: " << e.what() << std::endl;
    }
    
    std::cout << "\n=== Test 4: Base class exception ===" << std::endl;
    try {
        FunctionTryClass ftc(0, 1, 2);  // Base 构造会抛异常
    }
    catch (const std::exception& e) {
        std::cout << "Final catch: " << e.what() << std::endl;
    }
    
    std::cout << "\n=== Test 5: Regular function try block ===" << std::endl;
    regular_function(10);
    regular_function(-5);
    
    std::cout << "\n=== Test 6: Safe destructor ===" << std::endl;
    {
        SafeDestructor sd(-1);
    }  // 析构函数中的异常被安全捕获
    
    return 0;
}

/*
要点总结：
1. 构造函数函数try块主要用于捕获初始化列表中的异常
2. 构造函数的catch块中异常会自动重新抛出（除非显式throw其他异常）
3. 已构造的基类和成员在异常时会自动析构
4. 当前对象的析构函数不会被调用（因为对象未完全构造）
5. 析构函数应该是noexcept，内部捕获所有异常
6. 函数try块对普通函数也适用，但异常不会自动重新抛出
*/
```

由于内容较多，我将继续为您详细讲解剩余的C++特性。让我继续：

## 26. 模块 (Modules)

**标准版本**: C++20

**详细讲解**:
模块是C++20引入的重要特性，用于替代传统的头文件包含机制。模块提供更好的封装性、更快的编译速度、避免宏污染。模块接口单元使用 `export module` 声明，实现单元使用 `module` 声明。

**演示代码**:
```cpp
// math_module.cppm (模块接口单元)
export module math_utils;  // 声明模块名称

import std;  // C++23: 导入标准库模块

// 导出函数
export int add(int a, int b) {
    return a + b;
}

export int multiply(int a, int b) {
    return a * b;
}

// 不导出的内部函数（模块私有）
int internal_helper(int x) {
    return x * 2;
}

// 导出类
export class Calculator {
    int value_;
public:
    Calculator(int v = 0) : value_(v) {}
    
    int add(int x) {
        value_ += x;
        return value_;
    }
    
    int get_value() const {
        return value_;
    }
};

// 导出命名空间
export namespace math {
    constexpr double PI = 3.14159265359;
    
    double circle_area(double radius) {
        return PI * radius * radius;
    }
}

// math_advanced.cppm (另一个模块，依赖 math_utils)
export module math_advanced;

import math_utils;  // 导入其他模块

export double power(double base, int exp) {
    double result = 1.0;
    for (int i = 0; i < exp; ++i) {
        result = multiply(result, base);  // 使用导入的函数
    }
    return result;
}

// main.cpp (使用模块)
import math_utils;
import math_advanced;
#include <iostream>

int main() {
    std::cout << "10 + 20 = " << add(10, 20) << std::endl;
    std::cout << "10 * 20 = " << multiply(10, 20) << std::endl;
    
    Calculator calc(100);
    calc.add(50);
    std::cout << "Calculator value: " << calc.get_value() << std::endl;
    
    std::cout << "Circle area (r=5): " << math::circle_area(5.0) << std::endl;
    
    std::cout << "2^8 = " << power(2.0, 8) << std::endl;
    
    // internal_helper(10);  // 错误：未导出，不可访问
    
    return 0;
}

/*
模块的优势：
1. 更快的编译：模块只编译一次，避免重复解析头文件
2. 更好的封装：可以控制哪些声明被导出
3. 避免宏污染：模块不导出宏定义
4. 无需包含保护：不需要 #ifndef/#define/#endif
5. 导入顺序无关：不像头文件那样依赖包含顺序

模块结构：
- 模块接口单元：export module 模块名;
- 模块实现单元：module 模块名;
- 模块分区：export module 模块名:分区名;
- 全局模块片段：module; ... export module 模块名;
*/
```

## 27. 全局模块片段及其存在的意义

**标准版本**: C++20

**详细讲解**:
全局模块片段（Global Module Fragment）允许在模块接口中包含传统头文件，这些头文件的声明不会被导出。它的主要目的是兼容性：允许模块使用依赖传统头文件的代码，同时保持模块的封装性。

**演示代码**:
```cpp
// legacy_wrapper.cppm
module;  // 全局模块片段开始

// 在这里包含传统头文件
// 这些声明属于全局模块片段，不会被导出
#include <cstdio>
#include <cstring>
#define LEGACY_MACRO 42  // 宏定义不会泄露到模块外

// 可能包含第三方C库
extern "C" {
    // 假设这是某个C库的声明
    int legacy_function(const char* str);
}

export module legacy_wrapper;  // 全局模块片段结束，模块声明开始

import std;  // 导入标准库模块

// 包装传统C函数
export class FileWrapper {
    FILE* file_;
    
public:
    FileWrapper(const char* filename, const char* mode) {
        // 使用全局模块片段中的 stdio
        file_ = std::fopen(filename, mode);
    }
    
    ~FileWrapper() {
        if (file_) {
            std::fclose(file_);
        }
    }
    
    bool is_open() const {
        return file_ != nullptr;
    }
    
    void write(const std::string& text) {
        if (file_) {
            std::fputs(text.c_str(), file_);
        }
    }
};

// 使用全局模块片段中定义的宏（模块内部）
int get_magic_number() {
    return LEGACY_MACRO;  // 可以在模块内使用
}

export int process_string(const std::string& str) {
    // 使用 cstring 中的函数
    return std::strlen(str.c_str());
}

// main.cpp
import legacy_wrapper;
#include <iostream>

int main() {
    // LEGACY_MACRO  // 错误：宏未导出，外部不可见
    
    FileWrapper fw("test.txt", "w");
    if (fw.is_open()) {
        fw.write("Hello from module!\n");
        std::cout << "File written successfully" << std::endl;
    }
    
    std::cout << "String length: " 
              << process_string("Hello") << std::endl;
    
    return 0;
}

/*
全局模块片段的意义：
1. 兼容性：允许模块使用传统C/C++库
2. 封装性：传统头文件的声明不会污染模块接口
3. 隔离宏：宏定义只在模块内部可见
4. 过渡方案：帮助逐步将代码迁移到模块系统

使用场景：
- 需要使用传统C库（如POSIX API）
- 依赖不支持模块的第三方库
- 包装传统代码以提供模块接口
- 使用预处理器宏但不想导出

注意事项：
- 全局模块片段必须在模块声明之前
- 只能包含预处理指令和声明
- 包含的内容不会被导出
- 应该尽量少用，优先使用模块化的解决方案
*/
```

## 28. 模块分区 (Module Partitions)

**标准版本**: C++20

**详细讲解**:
模块分区允许将大型模块分割成多个逻辑单元，提高代码组织性和编译并行性。分区可以是接口分区（导出）或实现分区（不导出）。主模块接口可以导出分区，使其对模块用户可见。

**演示代码**:
```cpp
// shapes.cppm (主模块接口)
export module shapes;

// 导出接口分区
export import :circle;
export import :rectangle;
export import :triangle;

// 不导出实现分区（仅模块内部使用）
import :internal_utils;

export namespace shapes {
    void print_all_info() {
        std::cout << "Shapes module loaded" << std::endl;
    }
}

// shapes-circle.cppm (接口分区)
export module shapes:circle;

import std;

export namespace shapes {
    class Circle {
        double radius_;
    public:
        Circle(double r) : radius_(r) {}
        
        double area() const {
            return 3.14159 * radius_ * radius_;
        }
        
        double perimeter() const {
            return 2 * 3.14159 * radius_;
        }
    };
}

// shapes-rectangle.cppm (接口分区)
export module shapes:rectangle;

import std;

export namespace shapes {
    class Rectangle {
        double width_;
        double height_;
    public:
        Rectangle(double w, double h) : width_(w), height_(h) {}
        
        double area() const {
            return width_ * height_;
        }
        
        double perimeter() const {
            return 2 * (width_ + height_);
        }
    };
}

// shapes-triangle.cppm (接口分区)
export module shapes:triangle;

import std;

export namespace shapes {
    class Triangle {
        double a_, b_, c_;
    public:
        Triangle(double a, double b, double c) : a_(a), b_(b), c_(c) {}
        
        double area() const {
            // 海伦公式
            double s = (a_ + b_ + c_) / 2;
            return std::sqrt(s * (s - a_) * (s - b_) * (s - c_));
        }
        
        double perimeter() const {
            return a_ + b_ + c_;
        }
    };
}

// shapes-internal.cppm (实现分区，不导出)
module shapes:internal_utils;

import std;

// 模块内部辅助函数
namespace shapes::internal {
    void log(const std::string& msg) {
        std::cout << "[shapes internal] " << msg << std::endl;
    }
    
    double round_to_decimals(double value, int decimals) {
        double factor = std::pow(10, decimals);
        return std::round(value * factor) / factor;
    }
}

// main.cpp
import shapes;
#include <iostream>

int main() {
    // 可以使用所有导出的分区
    shapes::Circle circle(5.0);
    shapes::Rectangle rect(4.0, 6.0);
    shapes::Triangle triangle(3.0, 4.0, 5.0);
    
    std::cout << "Circle area: " << circle.area() << std::endl;
    std::cout << "Rectangle area: " << rect.area() << std::endl;
    std::cout << "Triangle area: " << triangle.area() << std::endl;
    
    shapes::print_all_info();
    
    // shapes::internal::log("test");  // 错误：内部分区未导出
    
    return 0;
}

/*
模块分区的优势：
1. 代码组织：将大模块分成逻辑单元
2. 编译并行：分区可以并行编译
3. 选择性导出：控制哪些部分对外可见
4. 实现隐藏：实现分区不会暴露给模块用户

分区类型：
- 接口分区：export module 模块名:分区名;
- 实现分区：module 模块名:分区名;
- 主模块接口：export module 模块名;

导入分区：
- 导出分区：export import :分区名;
- 内部导入：import :分区名;

命名约定：
- 分区文件名：模块名-分区名.cppm
- 分区名使用冒号：module_name:partition_name
*/
```

## 29. CMake 中声明模块范围库

**标准版本**: C++20 模块，CMake 3.28+

**详细讲解**:
CMake 3.28+ 开始实验性支持C++20模块。需要设置 `CMAKE_CXX_STANDARD` 为20或23，并正确配置模块文件的依赖关系。

**演示代码**:
```cmake
# CMakeLists.txt
cmake_minimum_required(VERSION 3.28)
project(ModuleExample CXX)

# 启用 C++20 和模块支持
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 实验性启用模块支持
set(CMAKE_EXPERIMENTAL_CXX_MODULE_CMAKE_API "2182bf5c-ef0d-489a-91da-49dbc3090d2a")
set(CMAKE_EXPERIMENTAL_CXX_MODULE_DYNDEP ON)

# 定义模块库
add_library(math_module)

# 设置模块源文件
target_sources(math_module
    PUBLIC
        FILE_SET CXX_MODULES FILES
            math_utils.cppm        # 模块接口单元
            math_advanced.cppm     # 依赖的模块
)

# 可选：添加模块实现文件
# target_sources(math_module
#     PRIVATE
#         math_impl.cpp
# )

# 定义可执行文件
add_executable(app main.cpp)

# 链接模块库
target_link_libraries(app PRIVATE math_module)

# 更复杂的示例：带分区的模块
add_library(shapes_module)

target_sources(shapes_module
    PUBLIC
        FILE_SET CXX_MODULES FILES
            shapes.cppm              # 主模块接口
            shapes-circle.cppm       # 接口分区
            shapes-rectangle.cppm    # 接口分区
            shapes-triangle.cppm     # 接口分区
    PRIVATE
        FILE_SET CXX_MODULES FILES
            shapes-internal.cppm     # 实现分区
)

add_executable(shapes_app shapes_main.cpp)
target_link_libraries(shapes_app PRIVATE shapes_module)

# 安装模块
install(TARGETS math_module shapes_module
    EXPORT MyModulesTargets
    FILE_SET CXX_MODULES DESTINATION lib/modules
)

install(EXPORT MyModulesTargets
    FILE MyModulesTargets.cmake
    NAMESPACE MyProject::
    DESTINATION lib/cmake/MyProject
)
```

```cpp
// shapes_main.cpp (实际使用示例)
import shapes;
#include <iostream>
#include <format>  // C++20

int main() {
    shapes::Circle c(10.0);
    shapes::Rectangle r(5.0, 8.0);
    shapes::Triangle t(3.0, 4.0, 5.0);
    
    std::cout << std::format("Circle area: {:.2f}\n", c.area());
    std::cout << std::format("Rectangle area: {:.2f}\n", r.area());
    std::cout << std::format("Triangle area: {:.2f}\n", t.area());
    
    return 0;
}

/*
CMake 模块配置要点：

1. FILE_SET CXX_MODULES：
   - 用于指定模块源文件
   - PUBLIC：接口分区
   - PRIVATE：实现分区

2. 模块依赖：
   - CMake 自动检测模块间依赖
   - 确保编译顺序正确

3. 编译器支持：
   - GCC 11+
   - Clang 16+
   - MSVC 2022 17.5+

4. 注意事项：
   - 模块支持仍在实验阶段
   - 不同编译器行为可能不同
   - 建议使用最新版本的 CMake 和编译器

5. 替代方案（过渡期）：
   - 继续使用传统头文件
   - 混合使用模块和头文件
   - 等待工具链完全成熟
*/
```

## 30. 范围 (Ranges) 库

**标准版本**: C++20

**详细讲解**:
Ranges库是C++20的重大特性，提供了一套现代化的、组合式的算法和视图。支持惰性求值、管道语法、更安全的迭代器模型。核心概念包括范围（Range）、视图（View）、范围适配器、定制点对象（CPO）。

**演示代码**:
```cpp
#include <iostream>
#include <vector>
#include <ranges>
#include <algorithm>
#include <string>

namespace rng = std::ranges;
namespace vw = std::views;

int main() {
    std::vector<int> numbers = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
    
    // 1. 基本范围操作
    std::cout << "=== Basic Range Operations ===" << std::endl;
    
    // 传统方式
    for (auto it = numbers.begin(); it != numbers.end(); ++it) {
        std::cout << *it << " ";
    }
    std::cout << std::endl;
    
    // Ranges 方式
    for (auto n : numbers | vw::take(5)) {
        std::cout << n << " ";  // 只取前5个
    }
    std::cout << std::endl;
    
    // 2. 视图组合（管道语法）
    std::cout << "\n=== View Composition ===" << std::endl;
    
    auto even_squares = numbers 
        | vw::filter([](int n) { return n % 2 == 0; })  // 过滤偶数
        | vw::transform([](int n) { return n * n; });    // 平方
    
    for (auto n : even_squares) {
        std::cout << n << " ";  // 4 16 36 64 100
    }
    std::cout << std::endl;
    
    // 3. 惰性求值
    std::cout << "\n=== Lazy Evaluation ===" << std::endl;
    
    auto lazy_view = numbers
        | vw::transform([](int n) { 
            std::cout << "Transform " << n << std::endl; 
            return n * 2; 
        })
        | vw::take(3);  // 只会处理前3个
    
    std::cout << "Before iteration:" << std::endl;
    for (auto n : lazy_view) {
        std::cout << "Result: " << n << std::endl;
    }
    
    // 4. 常用视图
    std::cout << "\n=== Common Views ===" << std::endl;
    
    // iota: 生成序列
    for (auto n : vw::iota(1, 6)) {
        std::cout << n << " ";  // 1 2 3 4 5
    }
    std::cout << std::endl;
    
    // reverse: 反转
    for (auto n : numbers | vw::reverse | vw::take(3)) {
        std::cout << n << " ";  // 10 9 8
    }
    std::cout << std::endl;
    
    // drop: 跳过元素
    for (auto n : numbers | vw::drop(5)) {
        std::cout << n << " ";  // 6 7 8 9 10
    }
    std::cout << std::endl;
    
    // split: 分割
    std::string text = "hello world from ranges";
    for (auto word : text | vw::split(' ')) {
        for (char c : word) {
            std::cout << c;
        }
        std::cout << std::endl;
    }
    
    // 5. 范围算法
    std::cout << "\n=== Range Algorithms ===" << std::endl;
    
    std::vector<int> data = {3, 1, 4, 1, 5, 9, 2, 6};
    
    // 排序
    rng::sort(data);
    for (auto n : data) {
        std::cout << n << " ";
    }
    std::cout << std::endl;
    
    // 查找
    auto it = rng::find(data, 5);
    if (it != data.end()) {
        std::cout << "Found: " << *it << std::endl;
    }
    
    // 统计
    auto count = rng::count_if(data, [](int n) { return n > 3; });
    std::cout << "Count > 3: " << count << std::endl;
    
    // 6. 投影（Projection）
    std::cout << "\n=== Projections ===" << std::endl;
    
    struct Person {
        std::string name;
        int age;
    };
    
    std::vector<Person> people = {
        {"Alice", 30},
        {"Bob", 25},
        {"Charlie", 35}
    };
    
    // 按年龄排序
    rng::sort(people, {}, &Person::age);
    
    for (const auto& p : people) {
        std::cout << p.name << ": " << p.age << std::endl;
    }
    
    // 7. 视图材质化
    std::cout << "\n=== View Materialization ===" << std::endl;
    
    auto view = numbers | vw::filter([](int n) { return n % 2 == 0; });
    
    // 转换为容器
    std::vector<int> evens(view.begin(), view.end());
    // 或使用 ranges::to (C++23)
    // auto evens = view | std::ranges::to<std::vector>();
    
    for (auto n : evens) {
        std::cout << n << " ";
    }
    std::cout << std::endl;
    
    // 8. 复杂组合
    std::cout << "\n=== Complex Composition ===" << std::endl;
    
    auto result = vw::iota(1, 20)
        | vw::filter([](int n) { return n % 2 != 0; })  // 奇数
        | vw::transform([](int n) { return n * n; })     // 平方
        | vw::take(5)                                     // 前5个
        | vw::reverse;                                    // 反转
    
    for (auto n : result) {
        std::cout << n << " ";  // 81 49 25 9 1
    }
    std::cout << std::endl;
    
    return 0;
}

/*
Ranges 库的核心概念：

1. Range（范围）：
   - 可以被迭代的对象
   - 有 begin() 和 end()
   - 或有 begin() 和 sentinel

2. View（视图）：
   - 轻量级的范围
   - 常量时间复制
   - 惰性求值
   - 不拥有元素

3. Range Adaptor（范围适配器）：
   - 转换范围的可组合对象
   - 支持管道语法 |
   - 返回视图

4. 优势：
   - 更简洁的代码
   - 更好的可组合性
   - 惰性求值提高性能
   - 类型安全
   - 更好的错误消息

5. 常用视图：
   - filter: 过滤元素
   - transform: 转换元素
   - take/drop: 获取/丢弃元素
   - reverse: 反转
   - split: 分割
   - join: 连接
   - iota: 生成序列
*/
```

由于篇幅限制，我将继续为您讲解剩余的C++特性。让我继续：

## 31. 范围适配器、定制点对象(CPO)、Niebloid

**标准版本**: C++20

**详细讲解**:
- **范围适配器**：可组合的范围转换器，支持管道操作
- **定制点对象 (CPO, Customization Point Object)**：支持ADL和显式定制的函数对象
- **Niebloid**：阻止ADL的CPO，确保调用的是ranges命名空间中的版本

**演示代码**:
```cpp
#include <iostream>
#include <vector>
#include <ranges>
#include <algorithm>
#include <concepts>

namespace rng = std::ranges;
namespace vw = std::views;

// 1. 自定义范围适配器
template<typename Pred>
struct filter_adaptor {
    Pred pred;
    
    filter_adaptor(Pred p) : pred(std::move(p)) {}
    
    template<rng::viewable_range R>
    auto operator()(R&& r) const {
        return std::forward<R>(r) | vw::filter(pred);
    }
};

template<typename Pred>
auto my_filter(Pred pred) {
    return filter_adaptor<Pred>{std::move(pred)};
}

// 支持管道操作
template<rng::viewable_range R, typename Pred>
auto operator|(R&& r, filter_adaptor<Pred> adaptor) {
    return adaptor(std::forward<R>(r));
}

// 2. 自定义范围类型
class NumberRange {
    int start_;
    int end_;
    
public:
    NumberRange(int s, int e) : start_(s), end_(e) {}
    
    struct Iterator {
        int value;
        
        using value_type = int;
        using difference_type = std::ptrdiff_t;
        using iterator_category = std::forward_iterator_tag;
        
        int operator*() const { return value; }
        Iterator& operator++() { ++value; return *this; }
        Iterator operator++(int) { auto tmp = *this; ++value; return tmp; }
        bool operator==(const Iterator& other) const { return value == other.value; }
    };
    
    Iterator begin() const { return Iterator{start_}; }
    Iterator end() const { return Iterator{end_}; }
};

// 验证满足 range 概念
static_assert(rng::range<NumberRange>);
static_assert(rng::forward_range<NumberRange>);

// 3. 定制点对象示例
namespace custom {
    // 为自定义类型定制 begin/end
    class MyContainer {
        std::vector<int> data_;
    public:
        MyContainer(std::initializer_list<int> init) : data_(init) {}
        
        // 通过成员函数定制
        auto begin() { return data_.begin(); }
        auto end() { return data_.end(); }
        auto begin() const { return data_.begin(); }
        auto end() const { return data_.end(); }
        
        // 或通过友元函数定制（ADL）
        friend auto begin(MyContainer& c) { return c.data_.begin(); }
        friend auto end(MyContainer& c) { return c.data_.end(); }
    };
}

// 4. CPO 工作原理演示
namespace demo_cpo {
    // 简化的 begin CPO 实现
    namespace detail {
        struct begin_fn {
            // 1. 优先调用成员函数
            template<typename T>
            requires requires(T& t) { t.begin(); }
            auto operator()(T& t) const {
                std::cout << "Called member begin()" << std::endl;
                return t.begin();
            }
            
            // 2. 否则通过 ADL 查找
            template<typename T>
            requires (!requires(T& t) { t.begin(); } && 
                     requires(T& t) { begin(t); })
            auto operator()(T& t) const {
                std::cout << "Called ADL begin()" << std::endl;
                return begin(t);
            }
            
            // 3. 最后处理内建数组
            template<typename T, std::size_t N>
            auto operator()(T (&arr)[N]) const {
                std::cout << "Called array begin()" << std::endl;
                return arr + 0;
            }
        };
    }
    
    inline constexpr detail::begin_fn begin{};
}

// 5. Niebloid 示例（ranges::sort 就是 niebloid）
namespace demo_niebloid {
    struct sort_fn {
        // 不会触发 ADL，因为是函数对象调用
        template<rng::random_access_range R>
        void operator()(R&& r) const {
            std::cout << "ranges::sort called" << std::endl;
            rng::sort(r);
        }
        
        template<rng::random_access_range R, typename Comp>
        void operator()(R&& r, Comp comp) const {
            std::cout << "ranges::sort with comparator called" << std::endl;
            rng::sort(r, comp);
        }
    };
    
    inline constexpr sort_fn sort{};
}

int main() {
    std::vector<int> numbers = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
    
    // 1. 使用自定义范围适配器
    std::cout << "=== Custom Range Adaptor ===" << std::endl;
    auto evens = numbers | my_filter([](int n) { return n % 2 == 0; });
    for (auto n : evens) {
        std::cout << n << " ";
    }
    std::cout << std::endl;
    
    // 2. 使用自定义范围
    std::cout << "\n=== Custom Range ===" << std::endl;
    NumberRange range(1, 11);
    for (auto n : range | vw::filter([](int n) { return n % 2 != 0; })) {
        std::cout << n << " ";
    }
    std::cout << std::endl;
    
    // 3. 定制点对象
    std::cout << "\n=== Customization Point Objects ===" << std::endl;
    custom::MyContainer container{1, 2, 3, 4, 5};
    
    // ranges::begin 是 CPO，会根据情况调用正确的版本
    auto it = rng::begin(container);
    std::cout << "First element: " << *it << std::endl;
    
    // 4. CPO 工作原理
    std::cout << "\n=== CPO Mechanism ===" << std::endl;
    demo_cpo::begin(container);  // 调用成员函数
    
    int arr[] = {1, 2, 3};
    demo_cpo::begin(arr);  // 调用数组版本
    
    // 5. Niebloid 防止 ADL
    std::cout << "\n=== Niebloid ===" << std::endl;
    std::vector<int> data = {3, 1, 4, 1, 5};
    demo_niebloid::sort(data);  // 不会触发 ADL
    
    for (auto n : data) {
        std::cout << n << " ";
    }
    std::cout << std::endl
