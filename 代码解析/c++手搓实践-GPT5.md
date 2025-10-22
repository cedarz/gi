> 我在准备c++的面试，我希望你帮助我提高c++知识水平和面试技能，目前我能想到的面试内容可能有，手写线程池、内存分配、shared_ptr等等。请你罗列更多尽可能多的可能面试中会涉及到且在实际工作中比较常用的技术，要求把这些内容，按序列号，给出讲解和代码实现，输出为markdown格式，以便我后续导出整理。对于其他这里没有提及，而你认为对于c++从业者或者面试者比较重要的特性和技术点，也请一并罗列讲解并整理。

# 现代 C++ 面试与实战知识地图（讲解 + 代码示例）

说明与使用建议：
- 语言标准：本文示例默认基于 C++20（部分主题标注了 C++23）。
- 编译建议：g++/clang++ -std=c++20 -O2 -Wall -Wextra -Wpedantic
- 每个示例代码块均可作为“独立文件”编译运行；如需整合，请分离重复的 main 或改为单元测试方式。
- 内容聚焦“面试高频 + 实战常用”，覆盖语言机制、标准库、并发、工程化等。

---

1) RAII 与 Scope Guard（资源即对象）
- 讲解：RAII 通过对象生命周期管理资源（内存、文件、锁）。Scope Guard 用于在作用域结束时执行清理。
```cpp
#include <iostream>
#include <functional>

class ScopeGuard {
    std::function<void()> f_;
    bool active_ = true;
public:
    explicit ScopeGuard(std::function<void()> f) : f_(std::move(f)) {}
    ~ScopeGuard() { if (active_ && f_) f_(); }
    void dismiss() noexcept { active_ = false; }
};
int main() {
    std::cout << "start\n";
    ScopeGuard g([]{ std::cout << "cleanup on scope exit\n"; });
    std::cout << "work\n";
} // 自动执行 cleanup
```

2) Rule of Zero/Three/Five（拷贝/移动语义）
- 讲解：资源管理类需自定义析构/拷贝/移动（Rule of Five）；纯值类型尽量 Rule of Zero。
```cpp
#include <cstring>
#include <iostream>

class Buffer {
    size_t n_{};
    char* p_{};
public:
    Buffer() = default;
    explicit Buffer(size_t n): n_(n), p_(new char[n]) {}
    ~Buffer(){ delete[] p_; }

    Buffer(const Buffer& other): n_(other.n_), p_(new char[n_]) { std::memcpy(p_, other.p_, n_); }
    Buffer& operator=(const Buffer& other){
        if (this != &other) { Buffer tmp(other); swap(tmp); }
        return *this;
    }
    Buffer(Buffer&& other) noexcept : n_(other.n_), p_(other.p_) { other.n_=0; other.p_=nullptr; }
    Buffer& operator=(Buffer&& other) noexcept {
        if (this != &other) { delete[] p_; n_=other.n_; p_=other.p_; other.n_=0; other.p_=nullptr; }
        return *this;
    }
    void swap(Buffer& o) noexcept { std::swap(n_, o.n_); std::swap(p_, o.p_); }
};

int main(){
    Buffer a(1024), b;
    b = std::move(a);
    Buffer c = b; // 深拷贝
    (void)c;
}
```

3) 完美转发与 std::forward
- 讲解：保留参数值类别以避免不必要拷贝。
```cpp
#include <iostream>
#include <utility>
#include <vector>

template<class F, class... Args>
decltype(auto) call(F&& f, Args&&... args){
    return std::forward<F>(f)(std::forward<Args>(args)...);
}

int main(){
    std::vector<int> v;
    auto emplacer = [&](auto&&... xs){ (v.emplace_back(std::forward<decltype(xs)>(xs)), ...); };
    call(emplacer, 1, 2, 3);
    std::cout << v.size() << "\n";
}
```

4) 返回值优化/拷贝消除（RVO/NRVO）
- 讲解：返回局部对象时，通常省去拷贝/移动，提高性能。
```cpp
#include <iostream>

struct Big {
    Big(){ std::cout << "ctor\n"; }
    Big(const Big&){ std::cout << "copy\n"; }
    Big(Big&&) noexcept { std::cout << "move\n"; }
};

Big make(){
    Big b; // NRVO 典型场景
    return b;
}
int main(){ Big x = make(); }
```

5) 智能指针：unique_ptr/shared_ptr/weak_ptr
- 讲解：unique_ptr 独占所有权；shared_ptr 引用计数；weak_ptr 打破循环引用。
```cpp
#include <iostream>
#include <memory>

struct Node {
    int v{};
    std::shared_ptr<Node> next;      // 潜在循环
    std::weak_ptr<Node>   prev;      // 使用 weak_ptr 打破环
    explicit Node(int v): v(v) {}
};

int main(){
    auto a = std::make_shared<Node>(1);
    auto b = std::make_shared<Node>(2);
    a->next = b;
    b->prev = a; // 不增加计数，避免循环
    std::cout << "use_count(a)=" << a.use_count() << "\n"; // 1
}
```

6) enable_shared_from_this 正确获取自身 shared_ptr
- 讲解：避免从 this 构造新的 shared_ptr 造成双重控制块。
```cpp
#include <memory>
#include <iostream>

struct W : std::enable_shared_from_this<W> {
    std::shared_ptr<W> get() { return shared_from_this(); }
    void hello(){ std::cout << "hello\n"; }
};

int main(){
    auto p = std::make_shared<W>();
    auto q = p->get(); // 与 p 共享同一控制块
    q->hello();
    std::cout << p.use_count() << "\n"; // 2
}
```

7) 自定义删除器（文件句柄等）
- 讲解：unique_ptr 可管理非 new 资源。
```cpp
#include <cstdio>
#include <memory>
#include <stdexcept>

using UniqueFILE = std::unique_ptr<FILE, int(*)(FILE*)>;
int main(){
    UniqueFILE f(std::fopen("data.txt", "w"), &std::fclose);
    if (!f) throw std::runtime_error("open fail");
    std::fputs("hello\n", f.get());
}
```

8) placement new 与手动析构
- 讲解：在已分配的原始内存上构造对象，常用于内存池。
```cpp
#include <new>
#include <iostream>

struct X { int a; X(int x): a(x) { std::cout << "ctor\n"; } ~X(){ std::cout << "dtor\n"; } };

int main(){
    void* raw = ::operator new(sizeof(X), std::align_val_t(alignof(X)));
    X* px = new(raw) X(42);      // placement new
    std::cout << px->a << "\n";
    px->~X();                    // 手动析构
    ::operator delete(raw, std::align_val_t(alignof(X)));
}
```

9) 自定义（计数）分配器（Allocator）
- 讲解：用于统计/控制容器内存分配。
```cpp
#include <atomic>
#include <memory>
#include <vector>
#include <iostream>

template<class T>
struct CountingAllocator {
    using value_type = T;
    static inline std::atomic<size_t> bytes{0};

    T* allocate(std::size_t n){
        bytes += n * sizeof(T);
        return static_cast<T*>(::operator new(n * sizeof(T)));
    }
    void deallocate(T* p, std::size_t n) noexcept {
        bytes -= n * sizeof(T);
        ::operator delete(p);
    }
    template<class U> struct rebind { using other = CountingAllocator<U>; };
    bool operator==(const CountingAllocator&) const noexcept { return true; }
    bool operator!=(const CountingAllocator&) const noexcept { return false; }
};

int main(){
    std::vector<int, CountingAllocator<int>> v;
    v.reserve(1000);
    std::cout << "bytes=" << CountingAllocator<int>::bytes.load() << "\n";
}
```

10) 对象切片与虚函数
- 讲解：按值传递基类会切片；应以引用/指针多态。
```cpp
#include <iostream>

struct Base { virtual void f() const { std::cout << "Base\n"; } virtual ~Base()=default; };
struct Derived : Base { void f() const override { std::cout << "Derived\n"; } };

void call_by_value(Base b){ b.f(); }       // 切片，b 已不再是 Derived
void call_by_ref(const Base& b){ b.f(); }  // 正确多态

int main(){
    Derived d;
    call_by_value(d); // Base
    call_by_ref(d);   // Derived
}
```

11) PIMPL 惯用法（稳定 ABI/隐藏实现）
- 讲解：头文件仅暴露指针，减少编译依赖，隐藏成员。
```cpp
#include <memory>
#include <string>
#include <iostream>

class Widget {
public:
    Widget();
    ~Widget();
    void set(std::string s);
    void print() const;
private:
    struct Impl;
    std::unique_ptr<Impl> p_;
};

struct Widget::Impl {
    std::string payload;
    void print() const { std::cout << payload << "\n"; }
};

Widget::Widget(): p_(std::make_unique<Impl>()) {}
Widget::~Widget() = default;
void Widget::set(std::string s){ p_->payload = std::move(s); }
void Widget::print() const { p_->print(); }

int main(){ Widget w; w.set("pimpl"); w.print(); }
```

12) CRTP（静态多态/零开销）
- 讲解：编译期绑定，避免虚函数开销，便于复用。
```cpp
#include <iostream>

template<class D>
struct Addable {
    friend D operator+(D a, const D& b){ a += b; return a; }
};

struct Vec2 : Addable<Vec2> {
    float x{}, y{};
    Vec2& operator+=(const Vec2& o){ x+=o.x; y+=o.y; return *this; }
};

int main(){ Vec2 a{1,2}, b{3,4}; auto c = a + b; std::cout << c.x << "," << c.y << "\n"; }
```

13) constexpr/consteval/if constexpr
- 讲解：编译期计算与分支选择。
```cpp
#include <type_traits>
#include <array>
#include <iostream>

consteval int fib(int n){ return n<=1? n : fib(n-1)+fib(n-2); }

template<class T>
void print_kind(){
    if constexpr (std::is_integral_v<T>) std::cout << "integral\n";
    else std::cout << "other\n";
}

int main(){
    static_assert(fib(10) == 55);
    print_kind<int>(); print_kind<double>();
    constexpr auto a = std::array{1,2,3}; (void)a;
}
```

14) Concepts 与 requires（替代 SFINAE 的现代方式）
- 讲解：用约束表达接口意图，错误信息更友好。
```cpp
#include <concepts>
#include <iostream>

template<class T>
concept Incrementable = requires(T x){ ++x; x++; };

template<Incrementable T>
void inc(T& x){ ++x; }

int main(){
    int x=1; inc(x); std::cout << x << "\n";
    // std::string s; inc(s); // 不满足概念，编译期报错
}
```

15) type_traits 常用套路
- 讲解：萃取特性、做编译期分支/选择。
```cpp
#include <type_traits>
#include <iostream>

template<class T>
void foo(const T&){
    if constexpr (std::is_trivially_copyable_v<T>)
        std::cout << "trivial copyable\n";
    else
        std::cout << "non-trivial\n";
}
int main(){ struct X{X(){} X(const X&){} }; foo<int>(); foo<X>(); }
```

16) Ranges 管道式算法
- 讲解：可读性强、惰性计算、组合变换。
```cpp
#include <ranges>
#include <vector>
#include <iostream>

int main(){
    std::vector<int> v{1,2,3,4,5,6};
    auto view = v | std::views::filter([](int x){return x%2==0;})
                  | std::views::transform([](int x){return x*x;});
    for (int x : view) std::cout << x << " "; // 4 16 36
}
```

17) optional/variant/any（值语义和代数数据类型）
- 讲解：optional 表示可空值；variant 替代层次多态；any 动态类型擦除。
```cpp
#include <optional>
#include <variant>
#include <any>
#include <iostream>

int main(){
    std::optional<int> oi = 42;
    if (oi) std::cout << *oi << "\n";

    std::variant<int, std::string> v = std::string("hi");
    std::visit([](auto&& x){ std::cout << x << "\n"; }, v);

    std::any a = 3.14;
    if (a.type() == typeid(double)) std::cout << std::any_cast<double>(a) << "\n";
}
```

18) string_view 生命周期与陷阱
- 讲解：不拥有数据，必须保证被引用字符序列活到视图使用完。
```cpp
#include <string>
#include <string_view>
#include <iostream>

std::string make(){
    return "hello world";
}
std::string_view bad(){
    std::string s = make();
    return std::string_view{s}; // 悬垂！返回后 s 销毁
}
std::string stable = "persistent";
std::string_view good(){ return std::string_view{stable}; }

int main(){
    // auto sv = bad(); // 未定义行为
    auto sv2 = good(); std::cout << sv2 << "\n";
}
```

19) chrono 计时与 RAII 计时器
- 讲解：性能测试与超时控制。
```cpp
#include <chrono>
#include <iostream>

struct Timer {
    std::chrono::steady_clock::time_point t = std::chrono::steady_clock::now();
    ~Timer(){
        auto d = std::chrono::steady_clock::now() - t;
        std::cout << "elapsed: " << std::chrono::duration_cast<std::chrono::microseconds>(d).count() << "us\n";
    }
};

int main(){
    Timer _; // 代码块结束自动打印耗时
    volatile long long s=0; for (int i=0;i<1000000;i++) s+=i;
}
```

20) filesystem 常见操作
- 讲解：遍历目录、路径拼接、文件大小。
```cpp
#include <filesystem>
#include <iostream>

int main(){
    namespace fs = std::filesystem;
    for (auto& e : fs::directory_iterator(".")){
        std::cout << e.path().filename().string();
        if (fs::is_regular_file(e)) std::cout << " size=" << fs::file_size(e);
        std::cout << "\n";
    }
}
```

21) 线程、互斥量与锁（lock_guard/unique_lock）
- 讲解：最基本并发原语。
```cpp
#include <thread>
#include <mutex>
#include <vector>
#include <iostream>

int main(){
    std::mutex m;
    int counter = 0;
    auto work = [&]{
        for (int i=0;i<100000;i++){
            std::lock_guard<std::mutex> lk(m);
            ++counter;
        }
    };
    std::vector<std::thread> ths;
    for (int i=0;i<4;i++) ths.emplace_back(work);
    for (auto& t: ths) t.join();
    std::cout << counter << "\n"; // 400000
}
```

22) 条件变量 condition_variable（生产者-消费者）
- 讲解：等待条件、避免忙等。
```cpp
#include <queue>
#include <mutex>
#include <condition_variable>
#include <thread>
#include <iostream>

int main(){
    std::queue<int> q;
    std::mutex m; std::condition_variable cv;
    bool done=false;

    std::thread producer([&]{
        for (int i=1;i<=5;i++){
            { std::lock_guard<std::mutex> lk(m); q.push(i); }
            cv.notify_one();
        }
        { std::lock_guard<std::mutex> lk(m); done=true; }
        cv.notify_all();
    });

    std::thread consumer([&]{
        while (true){
            std::unique_lock<std::mutex> lk(m);
            cv.wait(lk, [&]{ return !q.empty() || done; });
            while(!q.empty()){ std::cout << q.front() << " "; q.pop(); }
            if (done) break;
        }
    });

    producer.join(); consumer.join();
}
```

23) 原子操作与内存序（release/acquire）
- 讲解：建立同步先后关系，避免数据竞争。
```cpp
#include <atomic>
#include <thread>
#include <iostream>

std::atomic<bool> ready{false};
int data = 0;

int main(){
    std::thread writer([]{
        data = 42;
        ready.store(true, std::memory_order_release);
    });
    std::thread reader([]{
        while (!ready.load(std::memory_order_acquire)) {}
        std::cout << data << "\n"; // 必然看到 42
    });
    writer.join(); reader.join();
}
```

24) 伪共享与对齐（避免共享缓存行）
- 讲解：相邻热点数据导致缓存抖动，可 alignas(64) 分离。
```cpp
#include <atomic>
#include <thread>
#include <iostream>

struct alignas(64) Counter { std::atomic<long> v{0}; };
int main(){
    Counter a, b;
    std::thread t1([&]{ for (long i=0;i<1'000'000;i++) a.v.fetch_add(1, std::memory_order_relaxed); });
    std::thread t2([&]{ for (long i=0;i<1'000'000;i++) b.v.fetch_add(1, std::memory_order_relaxed); });
    t1.join(); t2.join();
    std::cout << a.v << " " << b.v << "\n";
}
```

25) 无锁 SPSC 环形队列（单生产者单消费者）
- 讲解：仅一读一写时可用简单原子 + release/acquire。
```cpp
#include <atomic>
#include <optional>
#include <thread>
#include <iostream>
#include <array>

template<typename T, size_t N>
struct SPSC {
    static_assert(N > 1, "N>1");
    std::array<T, N> buf{};
    std::atomic<size_t> head{0}, tail{0}; // head:写入位置, tail:读取位置

    bool push(const T& v){
        size_t h = head.load(std::memory_order_relaxed);
        size_t n = (h + 1) % N;
        if (n == tail.load(std::memory_order_acquire)) return false; // full
        buf[h] = v;
        head.store(n, std::memory_order_release);
        return true;
    }
    std::optional<T> pop(){
        size_t t = tail.load(std::memory_order_relaxed);
        if (t == head.load(std::memory_order_acquire)) return std::nullopt; // empty
        T v = buf[t];
        tail.store((t+1)%N, std::memory_order_release);
        return v;
    }
};

int main(){
    SPSC<int, 1024> q;
    std::thread p([&]{ for (int i=1;i<=10000;i++) while(!q.push(i)){} });
    std::thread c([&]{ int cnt=0; while(cnt<10000){ if(auto x=q.pop()){ cnt++; } } std::cout << cnt << "\n"; });
    p.join(); c.join();
}
```

26) 线程池（任务队列 + futures）
- 讲解：常见面试手写点；注意停止、异常传播。
```cpp
#include <vector>
#include <thread>
#include <future>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <functional>

class ThreadPool {
    std::vector<std::thread> workers_;
    std::queue<std::function<void()>> tasks_;
    std::mutex m_;
    std::condition_variable cv_;
    bool stop_ = false;
public:
    explicit ThreadPool(size_t n = std::thread::hardware_concurrency()){
        for (size_t i=0;i<n;i++){
            workers_.emplace_back([this]{
                for(;;){
                    std::function<void()> task;
                    {
                        std::unique_lock<std::mutex> lk(m_);
                        cv_.wait(lk, [this]{ return stop_ || !tasks_.empty(); });
                        if (stop_ && tasks_.empty()) return;
                        task = std::move(tasks_.front()); tasks_.pop();
                    }
                    task();
                }
            });
        }
    }
    ~ThreadPool(){
        {
            std::lock_guard<std::mutex> lk(m_);
            stop_ = true;
        }
        cv_.notify_all();
        for (auto& t: workers_) t.join();
    }

    template<class F, class... Args>
    auto submit(F&& f, Args&&... args){
        using R = std::invoke_result_t<F, Args...>;
        auto pkg = std::make_shared<std::packaged_task<R()>>(
            std::bind(std::forward<F>(f), std::forward<Args>(args)...)
        );
        std::future<R> fut = pkg->get_future();
        {
            std::lock_guard<std::mutex> lk(m_);
            if (stop_) throw std::runtime_error("stopped");
            tasks_.emplace([pkg]{ (*pkg)(); });
        }
        cv_.notify_one();
        return fut;
    }
};

#include <iostream>
int main(){
    ThreadPool pool(4);
    auto f = pool.submit([](int a, int b){ return a + b; }, 1, 2);
    std::cout << f.get() << "\n";
}
```

27) future/promise（结果传递与同步）
- 讲解：手工建立异步结果通道。
```cpp
#include <future>
#include <thread>
#include <iostream>

int main(){
    std::promise<int> p;
    std::future<int> f = p.get_future();
    std::thread t([pr = std::move(p)]() mutable {
        pr.set_value(42);
    });
    std::cout << f.get() << "\n";
    t.join();
}
```

28) C++20 协程：最小生成器示例
- 讲解：co_yield/co_return；实际工程常配合库（演示自定义生成器）。
```cpp
#include <coroutine>
#include <iostream>
#include <optional>

template<typename T>
struct Generator {
    struct promise_type {
        T current;
        std::suspend_always yield_value(T value) noexcept { current = std::move(value); return {}; }
        std::suspend_always initial_suspend() noexcept { return {}; }
        std::suspend_always final_suspend() noexcept { return {}; }
        void return_void() {}
        void unhandled_exception(){ std::terminate(); }
        Generator get_return_object(){ return Generator{ std::coroutine_handle<promise_type>::from_promise(*this) }; }
    };
    std::coroutine_handle<promise_type> h;
    explicit Generator(std::coroutine_handle<promise_type> h): h(h) {}
    Generator(Generator&& o) noexcept : h(std::exchange(o.h, {})) {}
    ~Generator(){ if (h) h.destroy(); }
    std::optional<T> next(){
        if (!h || h.done()) return std::nullopt;
        h.resume();
        if (h.done()) return std::nullopt;
        return h.promise().current;
    }
};

Generator<int> counter(int n){
    for (int i=1;i<=n;i++) co_yield i;
}

int main(){
    auto g = counter(5);
    while (auto v = g.next()) std::cout << *v << " ";
}
```

29) 并行算法（execution::par）
- 讲解：易用的并行化入口（实现依赖于标准库）。
```cpp
#include <execution>
#include <vector>
#include <numeric>
#include <iostream>

int main(){
    std::vector<int> v(1'000'000, 1);
    long long s = std::reduce(std::execution::par, v.begin(), v.end(), 0LL);
    std::cout << s << "\n";
}
```

30) LRU 缓存（list + unordered_map）
- 讲解：O(1) 读写、淘汰最久未使用。
```cpp
#include <list>
#include <unordered_map>
#include <optional>
#include <iostream>

template<class K, class V>
class LRU {
    using It = typename std::list<std::pair<K,V>>::iterator;
    size_t cap_;
    std::list<std::pair<K,V>> lst_;
    std::unordered_map<K, It> pos_;
public:
    explicit LRU(size_t cap): cap_(cap) {}
    std::optional<V> get(const K& k){
        auto it = pos_.find(k);
        if (it == pos_.end()) return std::nullopt;
        lst_.splice(lst_.begin(), lst_, it->second);
        return it->second->second;
    }
    void put(K k, V v){
        auto it = pos_.find(k);
        if (it != pos_.end()){
            it->second->second = std::move(v);
            lst_.splice(lst_.begin(), lst_, it->second);
        } else {
            lst_.emplace_front(std::move(k), std::move(v));
            pos_[lst_.front().first] = lst_.begin();
            if (pos_.size() > cap_){
                auto& back = lst_.back();
                pos_.erase(back.first);
                lst_.pop_back();
            }
        }
    }
};

int main(){
    LRU<int,int> cache(2);
    cache.put(1,10); cache.put(2,20);
    std::cout << *cache.get(1) << "\n"; // 10
    cache.put(3,30); // 淘汰 2
    std::cout << (cache.get(2).has_value() ? 1 : 0) << "\n"; // 0
}
```

31) 自定义哈希（unordered_* 自定义类型）
- 讲解：提供 == 与 std::hash 特化。
```cpp
#include <unordered_set>
#include <functional>
#include <iostream>

struct Point { int x,y; };
bool operator==(const Point& a, const Point& b){ return a.x==b.x && a.y==b.y; }

namespace std {
template<> struct hash<Point> {
    size_t operator()(const Point& p) const noexcept {
        return (std::hash<int>{}(p.x)*1315423911u) ^ std::hash<int>{}(p.y);
    }
};
}

int main(){
    std::unordered_set<Point> s;
    s.insert({1,2});
    std::cout << s.count({1,2}) << "\n";
}
```

32) std::format（现代格式化）
- 讲解：类型安全、可本地化；注意编译器/标准库支持。
```cpp
#include <format>
#include <iostream>
#include <string>

int main(){
    std::string name = "Alice";
    int n = 3;
    std::cout << std::format("Hello {}, you have {} messages.\n", name, n);
    std::cout << std::format("{:.2f}\n", 3.1415926);
}
```

33) 简单线程安全日志（互斥 + 时间戳）
- 讲解：避免多线程交叉输出；真实工程建议异步队列。
```cpp
#include <mutex>
#include <iostream>
#include <chrono>
#include <sstream>
#include <thread>

class Logger {
    std::mutex m_;
public:
    template<class... Args>
    void log(Args&&... args){
        std::lock_guard<std::mutex> lk(m_);
        auto t = std::chrono::system_clock::to_time_t(std::chrono::system_clock::now());
        std::tm tm{}; 
        #if defined(_WIN32)
            localtime_s(&tm, &t);
        #else
            localtime_r(&t, &tm);
        #endif
        std::ostringstream os;
        os << "[" << std::put_time(&tm, "%F %T") << "] ";
        (os << ... << args) << "\n";
        std::cout << os.str();
    }
};

int main(){
    Logger log;
    std::thread a([&]{ log.log("from A ", 1); });
    std::thread b([&]{ log.log("from B ", 2); });
    a.join(); b.join();
}
```

34) 异常、安全性与 noexcept
- 讲解：noexcept 承诺不抛；违背将终止。RAII 确保异常情况下资源释放。
```cpp
#include <iostream>
#include <stdexcept>

struct Guard{
    ~Guard(){ std::cout << "release\n"; }
};

void may_throw(bool t){
    Guard g;
    if (t) throw std::runtime_error("err");
    std::cout << "ok\n";
}

void must_not_throw() noexcept {
    // throw std::runtime_error("oops"); // 将调用 std::terminate()
}

int main(){
    try { may_throw(true); } catch(...) { std::cout << "caught\n"; }
    must_not_throw();
}
```

35) Meyers Singleton（线程安全的懒初始化）
- 讲解：函数内静态局部变量初始化线程安全（C++11+）。
```cpp
#include <iostream>

class Config {
    Config() = default;
public:
    static Config& instance(){
        static Config inst;
        return inst;
    }
    void hello(){ std::cout << "singleton\n"; }
};

int main(){ Config::instance().hello(); }
```

36) AoS vs SoA（数据导向性能）
- 讲解：结构的数组 vs 数组的结构；向量化/缓存友好。
```cpp
#include <vector>
#include <numeric>
#include <iostream>

struct ParticleAoS { float x,y,z,w; };
struct ParticlesSoA {
    std::vector<float> x,y,z,w;
};

int main(){
    // AoS 累加
    std::vector<ParticleAoS> a(1'000'000, {1,2,3,4});
    float sumA=0; for (auto& p: a) sumA += p.x;
    // SoA 累加（更连续）
    ParticlesSoA s; s.x.assign(1'000'000, 1.f);
    float sumS = std::accumulate(s.x.begin(), s.x.end(), 0.f);
    std::cout << sumA << " " << sumS << "\n";
}
```

37) 随机数与分布（正确使用 <random>）
- 讲解：分离引擎与分布、重用对象避免重播。
```cpp
#include <random>
#include <iostream>

int main(){
    std::mt19937 rng(std::random_device{}()); // 随机播种
    std::uniform_int_distribution<int> dist(1,6);
    for (int i=0;i<5;i++) std::cout << dist(rng) << " ";
}
```

38) C++20 模块（模块接口与使用）
- 讲解：更快构建、明确依赖；编译器支持需开启开关。
- 文件1：math.ixx（接口单元）
```cpp
export module math;

export int add(int a, int b){ return a+b; }
```
- 文件2：main.cpp（导入并使用）
```cpp
import math;
#include <iostream>
int main(){ std::cout << add(1,2) << "\n"; }
```

39) 工程化：CMake 与 Sanitizers
- 讲解：构建配置、调试工具集成（ASan/UBSan/TSan）。
```cmake
# CMakeLists.txt
cmake_minimum_required(VERSION 3.20)
project(demo LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
add_executable(demo main.cpp)
# 开启 AddressSanitizer + UndefinedBehaviorSanitizer（GCC/Clang）
if (CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
  target_compile_options(demo PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer -O1 -g)
  target_link_options(demo PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer)
endif()
```

40) 单元测试雏形（不依赖第三方）
- 讲解：在没有框架时也可快速校验。
```cpp
#include <cassert>
#include <iostream>

int add(int a, int b){ return a+b; }

int main(){
    assert(add(1,2) == 3);
    assert(add(-1,1) == 0);
    std::cout << "all tests passed\n";
}
```

---

加分主题（可再深入）
- 自定义内存池与对象池（结合 8/25）。
- 多线程任务图/工作窃取（ThreadPool 进阶）。
- 零拷贝 I/O、mmap 与文件 I/O 优化。
- ABI 稳定性、ODR、内联与模块边界设计（结合 11/38）。
- 静态分析（clang-tidy）、格式化（clang-format）与 CI。
- 数据竞争检测（-fsanitize=thread）与性能分析（perf, VTune）。

面试技巧建议
- 讲解时先给“定义/适用场景/常见坑”，再给“复杂度/内存/异常安全”与“代码示例”。
- 现场编码：先写最小可运行版本，补充异常安全与边界；添加断言与基本测试。
- 多问业务上下文：数据规模、延迟目标、平台约束，再给方案与权衡。

如需我为以上任意条目出“专项练习题 + 参考解法 + 代码评审清单”，告诉我序号或主题即可。