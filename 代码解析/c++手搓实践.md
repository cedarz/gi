> 我在准备c++的面试，我希望你帮助我提高c++知识水平和面试技能，目前我能想到的面试内容可能有，手写线程池、内存分配、shared_ptr等等。请你罗列更多尽可能多的可能面试中会涉及到且在实际工作中比较常用的技术，要求把这些内容，按序列号，给出讲解和代码实现，输出为markdown格式，以便我后续导出整理。对于其他这里没有提及，而你认为对于c++从业者或者面试者比较重要的特性和技术点，也请一并罗列讲解并整理。

# C++ 面试核心知识点详解

## 目录

- [C++ 面试核心知识点详解](#c-面试核心知识点详解)
  - [目录](#目录)
  - [1. 智能指针实现](#1-智能指针实现)
    - [知识点](#知识点)
    - [shared\_ptr实现](#shared_ptr实现)
    - [unique\_ptr实现](#unique_ptr实现)
    - [weak\_ptr实现](#weak_ptr实现)
  - [2. 线程池实现](#2-线程池实现)
    - [知识点](#知识点-1)
    - [完整线程池实现](#完整线程池实现)
  - [3. 内存池实现](#3-内存池实现)
    - [知识点](#知识点-2)
    - [简单内存池实现](#简单内存池实现)
  - [4. 单例模式](#4-单例模式)
    - [知识点](#知识点-3)
    - [多种单例实现](#多种单例实现)
  - [5. 生产者-消费者模型](#5-生产者-消费者模型)
    - [知识点](#知识点-4)
    - [完整实现](#完整实现)
  - [6. 读写锁实现](#6-读写锁实现)
    - [知识点](#知识点-5)
    - [读写锁实现](#读写锁实现)
  - [7. LRU缓存实现](#7-lru缓存实现)
    - [知识点](#知识点-6)
    - [LRU Cache实现](#lru-cache实现)
  - [8. 对象池实现](#8-对象池实现)
    - [知识点](#知识点-7)
    - [对象池实现](#对象池实现)
  - [9. RAII资源管理](#9-raii资源管理)
    - [知识点](#知识点-8)
    - [RAII包装器实现](#raii包装器实现)
  - [10. 移动语义与完美转发](#10-移动语义与完美转发)
    - [知识点](#知识点-9)
    - [完整示例](#完整示例)
  - [11. 类型萃取与SFINAE](#11-类型萃取与sfinae)
    - [知识点](#知识点-10)
    - [实现示例](#实现示例)
  - [12. 可变参数模板](#12-可变参数模板)
    - [知识点](#知识点-11)
    - [实现示例](#实现示例-1)
  - [13. 函数对象与lambda](#13-函数对象与lambda)
    - [知识点](#知识点-12)
    - [实现示例](#实现示例-2)
  - [14. 协程基础(C++20)](#14-协程基础c20)
    - [知识点](#知识点-13)
    - [实现示例](#实现示例-3)
  - [15. 无锁编程基础](#15-无锁编程基础)
    - [知识点](#知识点-14)
    - [实现示例](#实现示例-4)
  - [16. 虚函数与多态机制](#16-虚函数与多态机制)
    - [知识点](#知识点-15)
    - [实现示例](#实现示例-5)
  - [17. STL容器底层实现](#17-stl容器底层实现)
    - [知识点](#知识点-16)
    - [实现示例](#实现示例-6)
  - [18. 异常安全与RAII](#18-异常安全与raii)
    - [知识点](#知识点-17)
    - [实现示例](#实现示例-7)
  - [19. 模板元编程基础](#19-模板元编程基础)
    - [知识点](#知识点-18)
    - [实现示例](#实现示例-8)
  - [20. 引用计数与循环引用](#20-引用计数与循环引用)
    - [知识点](#知识点-19)
    - [实现示例](#实现示例-9)
  - [总结](#总结)

---

## 1. 智能指针实现

### 知识点
- RAII原则
- 引用计数
- 原子操作
- 移动语义

### shared_ptr实现

```cpp
#include <atomic>
#include <utility>

template<typename T>
class SharedPtr {
private:
    T* ptr_;
    std::atomic<size_t>* ref_count_;
    
    void release() {
        if (ref_count_ && --(*ref_count_) == 0) {
            delete ptr_;
            delete ref_count_;
            ptr_ = nullptr;
            ref_count_ = nullptr;
        }
    }
    
public:
    // 构造函数
    explicit SharedPtr(T* p = nullptr) 
        : ptr_(p), ref_count_(p ? new std::atomic<size_t>(1) : nullptr) {}
    
    // 拷贝构造
    SharedPtr(const SharedPtr& other) 
        : ptr_(other.ptr_), ref_count_(other.ref_count_) {
        if (ref_count_) {
            ++(*ref_count_);
        }
    }
    
    // 移动构造
    SharedPtr(SharedPtr&& other) noexcept 
        : ptr_(other.ptr_), ref_count_(other.ref_count_) {
        other.ptr_ = nullptr;
        other.ref_count_ = nullptr;
    }
    
    // 拷贝赋值
    SharedPtr& operator=(const SharedPtr& other) {
        if (this != &other) {
            release();
            ptr_ = other.ptr_;
            ref_count_ = other.ref_count_;
            if (ref_count_) {
                ++(*ref_count_);
            }
        }
        return *this;
    }
    
    // 移动赋值
    SharedPtr& operator=(SharedPtr&& other) noexcept {
        if (this != &other) {
            release();
            ptr_ = other.ptr_;
            ref_count_ = other.ref_count_;
            other.ptr_ = nullptr;
            other.ref_count_ = nullptr;
        }
        return *this;
    }
    
    // 析构函数
    ~SharedPtr() {
        release();
    }
    
    // 操作符重载
    T& operator*() const { return *ptr_; }
    T* operator->() const { return ptr_; }
    T* get() const { return ptr_; }
    
    // 引用计数
    size_t use_count() const {
        return ref_count_ ? ref_count_->load() : 0;
    }
    
    // 重置
    void reset(T* p = nullptr) {
        release();
        ptr_ = p;
        ref_count_ = p ? new std::atomic<size_t>(1) : nullptr;
    }
    
    explicit operator bool() const { return ptr_ != nullptr; }
};
```

### unique_ptr实现

```cpp
template<typename T>
class UniquePtr {
private:
    T* ptr_;
    
public:
    explicit UniquePtr(T* p = nullptr) : ptr_(p) {}
    
    // 禁止拷贝
    UniquePtr(const UniquePtr&) = delete;
    UniquePtr& operator=(const UniquePtr&) = delete;
    
    // 移动构造
    UniquePtr(UniquePtr&& other) noexcept : ptr_(other.ptr_) {
        other.ptr_ = nullptr;
    }
    
    // 移动赋值
    UniquePtr& operator=(UniquePtr&& other) noexcept {
        if (this != &other) {
            delete ptr_;
            ptr_ = other.ptr_;
            other.ptr_ = nullptr;
        }
        return *this;
    }
    
    ~UniquePtr() {
        delete ptr_;
    }
    
    T& operator*() const { return *ptr_; }
    T* operator->() const { return ptr_; }
    T* get() const { return ptr_; }
    
    T* release() {
        T* temp = ptr_;
        ptr_ = nullptr;
        return temp;
    }
    
    void reset(T* p = nullptr) {
        delete ptr_;
        ptr_ = p;
    }
    
    explicit operator bool() const { return ptr_ != nullptr; }
};
```

### weak_ptr实现

```cpp
template<typename T>
class WeakPtr {
private:
    T* ptr_;
    std::atomic<size_t>* ref_count_;
    
public:
    WeakPtr() : ptr_(nullptr), ref_count_(nullptr) {}
    
    WeakPtr(const SharedPtr<T>& sp) 
        : ptr_(sp.get()), ref_count_(sp.ref_count_) {}
    
    // 检查对象是否还存在
    bool expired() const {
        return !ref_count_ || ref_count_->load() == 0;
    }
    
    // 尝试获取SharedPtr
    SharedPtr<T> lock() const {
        return expired() ? SharedPtr<T>() : SharedPtr<T>(*this);
    }
};
```

---

## 2. 线程池实现

### 知识点
- 条件变量
- 互斥锁
- 任务队列
- 线程管理
- future/promise

### 完整线程池实现

```cpp
#include <vector>
#include <queue>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <functional>
#include <future>
#include <memory>

class ThreadPool {
private:
    std::vector<std::thread> workers_;           // 工作线程
    std::queue<std::function<void()>> tasks_;    // 任务队列
    std::mutex queue_mutex_;                      // 队列锁
    std::condition_variable condition_;           // 条件变量
    bool stop_;                                   // 停止标志
    
public:
    explicit ThreadPool(size_t thread_count) : stop_(false) {
        // 创建工作线程
        for (size_t i = 0; i < thread_count; ++i) {
            workers_.emplace_back([this] {
                while (true) {
                    std::function<void()> task;
                    {
                        std::unique_lock<std::mutex> lock(queue_mutex_);
                        
                        // 等待任务或停止信号
                        condition_.wait(lock, [this] {
                            return stop_ || !tasks_.empty();
                        });
                        
                        // 如果停止且队列为空，退出
                        if (stop_ && tasks_.empty()) {
                            return;
                        }
                        
                        // 取出任务
                        task = std::move(tasks_.front());
                        tasks_.pop();
                    }
                    
                    // 执行任务
                    task();
                }
            });
        }
    }
    
    // 提交任务
    template<typename F, typename... Args>
    auto submit(F&& f, Args&&... args) 
        -> std::future<typename std::result_of<F(Args...)>::type> {
        
        using return_type = typename std::result_of<F(Args...)>::type;
        
        // 创建packaged_task
        auto task = std::make_shared<std::packaged_task<return_type()>>(
            std::bind(std::forward<F>(f), std::forward<Args>(args)...)
        );
        
        std::future<return_type> res = task->get_future();
        
        {
            std::unique_lock<std::mutex> lock(queue_mutex_);
            
            if (stop_) {
                throw std::runtime_error("ThreadPool is stopped");
            }
            
            tasks_.emplace([task]() { (*task)(); });
        }
        
        condition_.notify_one();
        return res;
    }
    
    // 析构函数
    ~ThreadPool() {
        {
            std::unique_lock<std::mutex> lock(queue_mutex_);
            stop_ = true;
        }
        
        condition_.notify_all();
        
        for (std::thread& worker : workers_) {
            if (worker.joinable()) {
                worker.join();
            }
        }
    }
    
    // 获取待处理任务数
    size_t get_task_count() const {
        std::unique_lock<std::mutex> lock(queue_mutex_);
        return tasks_.size();
    }
};

// 使用示例
void example_threadpool() {
    ThreadPool pool(4);
    
    // 提交任务
    auto result = pool.submit([](int x, int y) {
        return x + y;
    }, 10, 20);
    
    std::cout << "Result: " << result.get() << std::endl;
}
```

---

## 3. 内存池实现

### 知识点
- 内存对齐
- 自由链表
- 内存块管理
- 防止内存碎片

### 简单内存池实现

```cpp
#include <cstddef>
#include <new>

class MemoryPool {
private:
    struct Block {
        Block* next;
    };
    
    Block* free_list_;        // 空闲块链表
    size_t block_size_;       // 块大小
    size_t block_count_;      // 每次分配的块数
    char* memory_start_;      // 当前内存块起始位置
    char* memory_end_;        // 当前内存块结束位置
    
    // 分配新的内存块
    void allocate_chunk() {
        size_t chunk_size = block_size_ * block_count_;
        memory_start_ = new char[chunk_size];
        memory_end_ = memory_start_ + chunk_size;
        
        // 将新分配的内存块链接到自由链表
        char* current = memory_start_;
        while (current + block_size_ <= memory_end_) {
            Block* block = reinterpret_cast<Block*>(current);
            block->next = free_list_;
            free_list_ = block;
            current += block_size_;
        }
    }
    
public:
    MemoryPool(size_t block_size, size_t block_count = 32)
        : free_list_(nullptr)
        , block_size_(block_size < sizeof(Block) ? sizeof(Block) : block_size)
        , block_count_(block_count)
        , memory_start_(nullptr)
        , memory_end_(nullptr) {
        allocate_chunk();
    }
    
    ~MemoryPool() {
        // 简化版本，实际应该追踪所有分配的chunk
        delete[] memory_start_;
    }
    
    // 分配内存
    void* allocate() {
        if (!free_list_) {
            allocate_chunk();
        }
        
        Block* block = free_list_;
        free_list_ = block->next;
        return block;
    }
    
    // 释放内存
    void deallocate(void* ptr) {
        if (!ptr) return;
        
        Block* block = static_cast<Block*>(ptr);
        block->next = free_list_;
        free_list_ = block;
    }
};

// 对象内存池
template<typename T>
class ObjectPool {
private:
    MemoryPool pool_;
    
public:
    ObjectPool(size_t block_count = 32) 
        : pool_(sizeof(T), block_count) {}
    
    template<typename... Args>
    T* construct(Args&&... args) {
        void* mem = pool_.allocate();
        return new(mem) T(std::forward<Args>(args)...);
    }
    
    void destroy(T* obj) {
        if (!obj) return;
        obj->~T();
        pool_.deallocate(obj);
    }
};
```

---

## 4. 单例模式

### 知识点
- 线程安全
- 懒加载
- 内存管理
- C++11特性

### 多种单例实现

```cpp
// 1. 懒汉式（线程安全，C++11）
class Singleton {
private:
    Singleton() {}
    ~Singleton() {}
    Singleton(const Singleton&) = delete;
    Singleton& operator=(const Singleton&) = delete;
    
public:
    static Singleton& get_instance() {
        static Singleton instance;  // C++11保证线程安全
        return instance;
    }
};

// 2. 饿汉式
class EagerSingleton {
private:
    static EagerSingleton instance_;
    
    EagerSingleton() {}
    ~EagerSingleton() {}
    EagerSingleton(const EagerSingleton&) = delete;
    EagerSingleton& operator=(const EagerSingleton&) = delete;
    
public:
    static EagerSingleton& get_instance() {
        return instance_;
    }
};

EagerSingleton EagerSingleton::instance_;

// 3. 双重检查锁定（DCLP）
#include <mutex>
#include <atomic>

class DCLSingleton {
private:
    static std::atomic<DCLSingleton*> instance_;
    static std::mutex mutex_;
    
    DCLSingleton() {}
    ~DCLSingleton() {}
    DCLSingleton(const DCLSingleton&) = delete;
    DCLSingleton& operator=(const DCLSingleton&) = delete;
    
public:
    static DCLSingleton* get_instance() {
        DCLSingleton* tmp = instance_.load(std::memory_order_acquire);
        if (tmp == nullptr) {
            std::lock_guard<std::mutex> lock(mutex_);
            tmp = instance_.load(std::memory_order_relaxed);
            if (tmp == nullptr) {
                tmp = new DCLSingleton();
                instance_.store(tmp, std::memory_order_release);
            }
        }
        return tmp;
    }
    
    static void destroy() {
        DCLSingleton* tmp = instance_.load(std::memory_order_acquire);
        if (tmp) {
            delete tmp;
            instance_.store(nullptr, std::memory_order_release);
        }
    }
};

std::atomic<DCLSingleton*> DCLSingleton::instance_(nullptr);
std::mutex DCLSingleton::mutex_;

// 4. 模板单例基类
template<typename T>
class SingletonBase {
protected:
    SingletonBase() {}
    ~SingletonBase() {}
    SingletonBase(const SingletonBase&) = delete;
    SingletonBase& operator=(const SingletonBase&) = delete;
    
public:
    static T& get_instance() {
        static T instance;
        return instance;
    }
};

// 使用示例
class MyClass : public SingletonBase<MyClass> {
    friend class SingletonBase<MyClass>;
private:
    MyClass() {}
public:
    void do_something() {}
};
```

---

## 5. 生产者-消费者模型

### 知识点
- 条件变量
- 互斥锁
- 线程同步
- RAII

### 完整实现

```cpp
#include <queue>
#include <mutex>
#include <condition_variable>
#include <thread>
#include <vector>
#include <iostream>

template<typename T>
class BlockingQueue {
private:
    std::queue<T> queue_;
    mutable std::mutex mutex_;
    std::condition_variable not_empty_;
    std::condition_variable not_full_;
    size_t capacity_;
    
public:
    explicit BlockingQueue(size_t capacity = 100) 
        : capacity_(capacity) {}
    
    // 生产
    void push(const T& item) {
        std::unique_lock<std::mutex> lock(mutex_);
        not_full_.wait(lock, [this] {
            return queue_.size() < capacity_;
        });
        
        queue_.push(item);
        not_empty_.notify_one();
    }
    
    void push(T&& item) {
        std::unique_lock<std::mutex> lock(mutex_);
        not_full_.wait(lock, [this] {
            return queue_.size() < capacity_;
        });
        
        queue_.push(std::move(item));
        not_empty_.notify_one();
    }
    
    // 消费
    T pop() {
        std::unique_lock<std::mutex> lock(mutex_);
        not_empty_.wait(lock, [this] {
            return !queue_.empty();
        });
        
        T item = std::move(queue_.front());
        queue_.pop();
        not_full_.notify_one();
        return item;
    }
    
    // 尝试消费（非阻塞）
    bool try_pop(T& item) {
        std::unique_lock<std::mutex> lock(mutex_);
        if (queue_.empty()) {
            return false;
        }
        
        item = std::move(queue_.front());
        queue_.pop();
        not_full_.notify_one();
        return true;
    }
    
    // 带超时的pop
    template<typename Rep, typename Period>
    bool pop_for(T& item, 
                 const std::chrono::duration<Rep, Period>& timeout) {
        std::unique_lock<std::mutex> lock(mutex_);
        if (!not_empty_.wait_for(lock, timeout, [this] {
            return !queue_.empty();
        })) {
            return false;
        }
        
        item = std::move(queue_.front());
        queue_.pop();
        not_full_.notify_one();
        return true;
    }
    
    size_t size() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return queue_.size();
    }
    
    bool empty() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return queue_.empty();
    }
};

// 使用示例
void producer_consumer_example() {
    BlockingQueue<int> queue(10);
    
    // 生产者
    std::thread producer([&queue]() {
        for (int i = 0; i < 100; ++i) {
            queue.push(i);
            std::cout << "Produced: " << i << std::endl;
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
    });
    
    // 消费者
    std::thread consumer([&queue]() {
        for (int i = 0; i < 100; ++i) {
            int item = queue.pop();
            std::cout << "Consumed: " << item << std::endl;
            std::this_thread::sleep_for(std::chrono::milliseconds(20));
        }
    });
    
    producer.join();
    consumer.join();
}
```

---

## 6. 读写锁实现

### 知识点
- 共享锁
- 独占锁
- 条件变量
- 线程同步

### 读写锁实现

```cpp
#include <mutex>
#include <condition_variable>

class ReadWriteLock {
private:
    std::mutex mutex_;
    std::condition_variable read_cv_;
    std::condition_variable write_cv_;
    int readers_;           // 当前读者数量
    int writers_;           // 当前写者数量
    int write_waiters_;     // 等待的写者数量
    
public:
    ReadWriteLock() 
        : readers_(0), writers_(0), write_waiters_(0) {}
    
    // 读锁
    void lock_read() {
        std::unique_lock<std::mutex> lock(mutex_);
        // 如果有写者或等待的写者，读者等待
        read_cv_.wait(lock, [this] {
            return writers_ == 0 && write_waiters_ == 0;
        });
        ++readers_;
    }
    
    void unlock_read() {
        std::unique_lock<std::mutex> lock(mutex_);
        --readers_;
        if (readers_ == 0) {
            write_cv_.notify_one();
        }
    }
    
    // 写锁
    void lock_write() {
        std::unique_lock<std::mutex> lock(mutex_);
        ++write_waiters_;
        write_cv_.wait(lock, [this] {
            return readers_ == 0 && writers_ == 0;
        });
        --write_waiters_;
        ++writers_;
    }
    
    void unlock_write() {
        std::unique_lock<std::mutex> lock(mutex_);
        --writers_;
        if (write_waiters_ > 0) {
            write_cv_.notify_one();
        } else {
            read_cv_.notify_all();
        }
    }
};

// RAII包装器
class ReadLock {
private:
    ReadWriteLock& rwlock_;
    
public:
    explicit ReadLock(ReadWriteLock& rwlock) : rwlock_(rwlock) {
        rwlock_.lock_read();
    }
    
    ~ReadLock() {
        rwlock_.unlock_read();
    }
};

class WriteLock {
private:
    ReadWriteLock& rwlock_;
    
public:
    explicit WriteLock(ReadWriteLock& rwlock) : rwlock_(rwlock) {
        rwlock_.lock_write();
    }
    
    ~WriteLock() {
        rwlock_.unlock_write();
    }
};

// 使用示例
void rwlock_example() {
    ReadWriteLock rwlock;
    int shared_data = 0;
    
    // 读线程
    std::thread reader([&rwlock, &shared_data]() {
        ReadLock lock(rwlock);
        std::cout << "Read: " << shared_data << std::endl;
    });
    
    // 写线程
    std::thread writer([&rwlock, &shared_data]() {
        WriteLock lock(rwlock);
        shared_data = 42;
        std::cout << "Write: " << shared_data << std::endl;
    });
    
    reader.join();
    writer.join();
}
```

---

## 7. LRU缓存实现

### 知识点
- 双向链表
- 哈希表
- 缓存淘汰策略
- STL容器

### LRU Cache实现

```cpp
#include <unordered_map>
#include <list>
#include <utility>

template<typename Key, typename Value>
class LRUCache {
private:
    size_t capacity_;
    std::list<std::pair<Key, Value>> cache_list_;  // 双向链表
    std::unordered_map<Key, 
        typename std::list<std::pair<Key, Value>>::iterator> cache_map_;
    
public:
    explicit LRUCache(size_t capacity) : capacity_(capacity) {}
    
    // 获取值
    Value get(const Key& key) {
        auto it = cache_map_.find(key);
        if (it == cache_map_.end()) {
            throw std::runtime_error("Key not found");
        }
        
        // 移动到链表头部（最近使用）
        cache_list_.splice(cache_list_.begin(), cache_list_, it->second);
        return it->second->second;
    }
    
    // 插入或更新
    void put(const Key& key, const Value& value) {
        auto it = cache_map_.find(key);
        
        if (it != cache_map_.end()) {
            // 更新现有值
            it->second->second = value;
            cache_list_.splice(cache_list_.begin(), cache_list_, it->second);
            return;
        }
        
        // 检查容量
        if (cache_list_.size() >= capacity_) {
            // 删除最久未使用的项（链表尾部）
            auto last = cache_list_.back();
            cache_map_.erase(last.first);
            cache_list_.pop_back();
        }
        
        // 插入新项到链表头部
        cache_list_.emplace_front(key, value);
        cache_map_[key] = cache_list_.begin();
    }
    
    // 检查键是否存在
    bool contains(const Key& key) const {
        return cache_map_.find(key) != cache_map_.end();
    }
    
    // 获取当前大小
    size_t size() const {
        return cache_list_.size();
    }
    
    // 清空缓存
    void clear() {
        cache_list_.clear();
        cache_map_.clear();
    }
};

// 使用示例
void lru_example() {
    LRUCache<int, std::string> cache(3);
    
    cache.put(1, "one");
    cache.put(2, "two");
    cache.put(3, "three");
    
    std::cout << cache.get(1) << std::endl;  // "one"
    
    cache.put(4, "four");  // 淘汰key=2
    
    try {
        cache.get(2);  // 抛出异常
    } catch (const std::exception& e) {
        std::cout << "Key 2 not found" << std::endl;
    }
}
```

---

## 8. 对象池实现

### 知识点
- 对象复用
- 内存管理
- RAII
- 智能指针

### 对象池实现

```cpp
#include <vector>
#include <memory>
#include <functional>
#include <mutex>

template<typename T>
class ObjectPool {
private:
    struct PoolDeleter {
        ObjectPool* pool;
        
        void operator()(T* obj) {
            if (pool) {
                pool->return_object(obj);
            } else {
                delete obj;
            }
        }
    };
    
public:
    using UniquePtr = std::unique_ptr<T, PoolDeleter>;
    
private:
    std::vector<std::unique_ptr<T>> pool_;
    std::mutex mutex_;
    size_t max_size_;
    std::function<std::unique_ptr<T>()> factory_;
    
public:
    explicit ObjectPool(size_t max_size = 100,
                       std::function<std::unique_ptr<T>()> factory = nullptr)
        : max_size_(max_size)
        , factory_(factory ? factory : []() { 
            return std::make_unique<T>(); 
        }) {}
    
    // 获取对象
    UniquePtr acquire() {
        std::lock_guard<std::mutex> lock(mutex_);
        
        if (pool_.empty()) {
            return UniquePtr(factory_().release(), PoolDeleter{this});
        }
        
        T* obj = pool_.back().release();
        pool_.pop_back();
        return UniquePtr(obj, PoolDeleter{this});
    }
    
    // 返还对象到池中
    void return_object(T* obj) {
        std::lock_guard<std::mutex> lock(mutex_);
        
        if (pool_.size() < max_size_) {
            pool_.emplace_back(obj);
        } else {
            delete obj;
        }
    }
    
    size_t size() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return pool_.size();
    }
    
    void clear() {
        std::lock_guard<std::mutex> lock(mutex_);
        pool_.clear();
    }
};

// 使用示例
class Connection {
public:
    Connection() {
        std::cout << "Connection created" << std::endl;
    }
    
    ~Connection() {
        std::cout << "Connection destroyed" << std::endl;
    }
    
    void execute(const std::string& query) {
        std::cout << "Executing: " << query << std::endl;
    }
};

void object_pool_example() {
    ObjectPool<Connection> pool(5);
    
    {
        auto conn = pool.acquire();
        conn->execute("SELECT * FROM users");
    } // 连接自动返回池中
    
    auto conn2 = pool.acquire();  // 复用之前的连接
    conn2->execute("INSERT INTO users VALUES (1, 'Alice')");
}
```

---

## 9. RAII资源管理

### 知识点
- 资源获取即初始化
- 异常安全
- 自动释放
- 智能指针

### RAII包装器实现

```cpp
#include <utility>
#include <functional>

// 通用RAII包装器
template<typename Resource, typename Deleter>
class RAIIWrapper {
private:
    Resource resource_;
    Deleter deleter_;
    bool owns_;
    
public:
    explicit RAIIWrapper(Resource resource, Deleter deleter)
        : resource_(resource), deleter_(deleter), owns_(true) {}
    
    ~RAIIWrapper() {
        if (owns_) {
            deleter_(resource_);
        }
    }
    
    // 禁止拷贝
    RAIIWrapper(const RAIIWrapper&) = delete;
    RAIIWrapper& operator=(const RAIIWrapper&) = delete;
    
    // 移动语义
    RAIIWrapper(RAIIWrapper&& other) noexcept
        : resource_(std::move(other.resource_))
        , deleter_(std::move(other.deleter_))
        , owns_(other.owns_) {
        other.owns_ = false;
    }
    
    RAIIWrapper& operator=(RAIIWrapper&& other) noexcept {
        if (this != &other) {
            if (owns_) {
                deleter_(resource_);
            }
            resource_ = std::move(other.resource_);
            deleter_ = std::move(other.deleter_);
            owns_ = other.owns_;
            other.owns_ = false;
        }
        return *this;
    }
    
    Resource& get() { return resource_; }
    const Resource& get() const { return resource_; }
    
    Resource release() {
        owns_ = false;
        return std::move(resource_);
    }
};

// 便捷函数
template<typename Resource, typename Deleter>
RAIIWrapper<Resource, Deleter> make_raii(Resource resource, Deleter deleter) {
    return RAIIWrapper<Resource, Deleter>(resource, deleter);
}

// 文件RAII包装
class FileHandle {
private:
    FILE* file_;
    
public:
    explicit FileHandle(const char* filename, const char* mode)
        : file_(fopen(filename, mode)) {
        if (!file_) {
            throw std::runtime_error("Failed to open file");
        }
    }
    
    ~FileHandle() {
        if (file_) {
            fclose(file_);
        }
    }
    
    FileHandle(const FileHandle&) = delete;
    FileHandle& operator=(const FileHandle&) = delete;
    
    FILE* get() const { return file_; }
};

// 锁RAII包装（类似lock_guard）
template<typename Mutex>
class LockGuard {
private:
    Mutex& mutex_;
    
public:
    explicit LockGuard(Mutex& mutex) : mutex_(mutex) {
        mutex_.lock();
    }
    
    ~LockGuard() {
        mutex_.unlock();
    }
    
    LockGuard(const LockGuard&) = delete;
    LockGuard& operator=(const LockGuard&) = delete;
};

// 作用域退出时执行清理
class ScopeExit {
private:
    std::function<void()> cleanup_;
    bool dismissed_;
    
public:
    explicit ScopeExit(std::function<void()> cleanup)
        : cleanup_(cleanup), dismissed_(false) {}
    
    ~ScopeExit() {
        if (!dismissed_) {
            cleanup_();
        }
    }
    
    void dismiss() { dismissed_ = true; }
    
    ScopeExit(const ScopeExit&) = delete;
    ScopeExit& operator=(const ScopeExit&) = delete;
};

// 使用示例
void raii_example() {
    // 文件RAII
    {
        FileHandle file("test.txt", "w");
        fprintf(file.get(), "Hello RAII\n");
    } // 文件自动关闭
    
    // 通用RAII
    auto handle = make_raii(
        malloc(1024),
        [](void* p) { free(p); }
    );
    
    // 作用域退出
    {
        ScopeExit cleanup([]() {
            std::cout << "Cleanup executed" << std::endl;
        });
        
        // 做一些工作...
    } // cleanup自动执行
}
```

---

## 10. 移动语义与完美转发

### 知识点
- 右值引用
- std::move
- std::forward
- 移动构造/赋值

### 完整示例

```cpp
#include <iostream>
#include <vector>
#include <string>
#include <utility>

// 演示移动语义的类
class MoveableResource {
private:
    int* data_;
    size_t size_;
    
public:
    // 构造函数
    explicit MoveableResource(size_t size = 0) 
        : data_(size > 0 ? new int[size] : nullptr)
        , size_(size) {
        std::cout << "Constructor: allocate " << size << " ints\n";
    }
    
    // 拷贝构造（深拷贝）
    MoveableResource(const MoveableResource& other)
        : data_(other.size_ > 0 ? new int[other.size_] : nullptr)
        , size_(other.size_) {
        std::cout << "Copy constructor: deep copy " << size_ << " ints\n";
        if (data_) {
            std::copy(other.data_, other.data_ + size_, data_);
        }
    }
    
    // 移动构造（浅拷贝，窃取资源）
    MoveableResource(MoveableResource&& other) noexcept
        : data_(other.data_)
        , size_(other.size_) {
        std::cout << "Move constructor: steal " << size_ << " ints\n";
        other.data_ = nullptr;
        other.size_ = 0;
    }
    
    // 拷贝赋值
    MoveableResource& operator=(const MoveableResource& other) {
        std::cout << "Copy assignment\n";
        if (this != &other) {
            delete[] data_;
            size_ = other.size_;
            data_ = size_ > 0 ? new int[size_] : nullptr;
            if (data_) {
                std::copy(other.data_, other.data_ + size_, data_);
            }
        }
        return *this;
    }
    
    // 移动赋值
    MoveableResource& operator=(MoveableResource&& other) noexcept {
        std::cout << "Move assignment\n";
        if (this != &other) {
            delete[] data_;
            data_ = other.data_;
            size_ = other.size_;
            other.data_ = nullptr;
            other.size_ = 0;
        }
        return *this;
    }
    
    ~MoveableResource() {
        std::cout << "Destructor: deallocate " << size_ << " ints\n";
        delete[] data_;
    }
    
    size_t size() const { return size_; }
};

// 完美转发示例
template<typename T, typename... Args>
std::unique_ptr<T> make_unique_impl(Args&&... args) {
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
}

// 万能引用与引用折叠
template<typename T>
void process(T&& arg) {
    // T&&是万能引用（转发引用）
    // 如果传入左值，T推导为X&，T&& -> X& && -> X&
    // 如果传入右值，T推导为X，T&& -> X&&
    
    std::cout << "Processing: ";
    if (std::is_lvalue_reference<T>::value) {
        std::cout << "lvalue reference\n";
    } else {
        std::cout << "rvalue reference\n";
    }
}

// 移动语义使用示例
class Widget {
private:
    std::vector<int> data_;
    std::string name_;
    
public:
    Widget(std::vector<int> data, std::string name)
        : data_(std::move(data))      // 移动构造
        , name_(std::move(name)) {    // 移动构造
    }
    
    // 成员函数也可以有左值和右值版本
    std::vector<int>& get_data() & {
        return data_;
    }
    
    std::vector<int> get_data() && {
        return std::move(data_);  // 移动返回
    }
};

void move_semantics_example() {
    // 移动构造
    MoveableResource res1(100);
    MoveableResource res2 = std::move(res1);  // 调用移动构造
    
    // 移动赋值
    MoveableResource res3(50);
    res3 = std::move(res2);  // 调用移动赋值
    
    // 完美转发
    int x = 42;
    process(x);           // 左值
    process(100);         // 右值
    process(std::move(x)); // 右值
    
    // 容器优化
    std::vector<MoveableResource> vec;
    vec.reserve(10);
    vec.push_back(MoveableResource(1000));  // 移动构造
    vec.emplace_back(2000);                 // 原地构造
}
```

---

## 11. 类型萃取与SFINAE

### 知识点
- 模板元编程
- SFINAE（替换失败不是错误）
- type_traits
- enable_if

### 实现示例

```cpp
#include <type_traits>
#include <iostream>
#include <vector>
#include <list>

// 1. 基础类型萃取
template<typename T>
struct TypeTraits {
    using value_type = T;
    using pointer = T*;
    using reference = T&;
    
    static constexpr bool is_pointer = false;
    static constexpr bool is_integral = std::is_integral<T>::value;
};

// 指针特化
template<typename T>
struct TypeTraits<T*> {
    using value_type = T;
    using pointer = T*;
    using reference = T&;
    
    static constexpr bool is_pointer = true;
    static constexpr bool is_integral = false;
};

// 2. 检测成员函数
template<typename T>
class HasToString {
private:
    template<typename U>
    static auto test(int) -> decltype(std::declval<U>().toString(), std::true_type{});
    
    template<typename>
    static std::false_type test(...);
    
public:
    static constexpr bool value = decltype(test<T>(0))::value;
};

// 3. SFINAE示例 - enable_if
// 只对整数类型有效
template<typename T>
typename std::enable_if<std::is_integral<T>::value, T>::type
add(T a, T b) {
    return a + b;
}

// 只对浮点类型有效
template<typename T>
typename std::enable_if<std::is_floating_point<T>::value, T>::type
add(T a, T b) {
    std::cout << "Float addition\n";
    return a + b;
}

// 4. 概念模拟（C++20之前）
template<typename T>
struct is_container {
private:
    template<typename U>
    static auto test(int) -> decltype(
        std::declval<U>().begin(),
        std::declval<U>().end(),
        std::declval<U>().size(),
        std::true_type{}
    );
    
    template<typename>
    static std::false_type test(...);
    
public:
    static constexpr bool value = decltype(test<T>(0))::value;
};

// 只对容器有效的函数
template<typename Container>
typename std::enable_if<is_container<Container>::value, void>::type
print_container(const Container& c) {
    for (const auto& item : c) {
        std::cout << item << " ";
    }
    std::cout << "\n";
}

// 5. if constexpr (C++17)
template<typename T>
auto get_value(T t) {
    if constexpr (std::is_pointer<T>::value) {
        return *t;  // 解引用指针
    } else {
        return t;   // 直接返回值
    }
}

// 6. 标签分派
struct integral_tag {};
struct floating_tag {};

template<typename T>
void process_impl(T value, integral_tag) {
    std::cout << "Processing integral: " << value << "\n";
}

template<typename T>
void process_impl(T value, floating_tag) {
    std::cout << "Processing floating: " << value << "\n";
}

template<typename T>
void process(T value) {
    using tag = typename std::conditional<
        std::is_integral<T>::value,
        integral_tag,
        floating_tag
    >::type;
    
    process_impl(value, tag{});
}

// 7. 自定义type_traits
template<typename T>
struct remove_const_ref {
    using type = typename std::remove_const<
        typename std::remove_reference<T>::type
    >::type;
};

template<typename T>
using remove_const_ref_t = typename remove_const_ref<T>::type;

// 使用示例
void type_traits_example() {
    // 类型萃取
    std::cout << "Is int integral: " 
              << TypeTraits<int>::is_integral << "\n";
    std::cout << "Is int* pointer: " 
              << TypeTraits<int*>::is_pointer << "\n";
    
    // 成员函数检测
    class WithToString {
    public:
        std::string toString() { return "WithToString"; }
    };
    
    std::cout << "HasToString: " 
              << HasToString<WithToString>::value << "\n";
    
    // SFINAE
    std::cout << add(1, 2) << "\n";      // 整数版本
    std::cout << add(1.5, 2.5) << "\n";  // 浮点版本
    
    // 容器检测
    std::vector<int> vec = {1, 2, 3, 4, 5};
    print_container(vec);
    
    // 标签分派
    process(42);      // 整数
    process(3.14);    // 浮点
}
```

---

## 12. 可变参数模板

### 知识点
- 参数包
- 参数包展开
- 递归模板
- fold表达式（C++17）

### 实现示例

```cpp
#include <iostream>
#include <tuple>
#include <utility>

// 1. 基础递归展开
template<typename T>
void print(const T& value) {
    std::cout << value << "\n";
}

template<typename T, typename... Args>
void print(const T& value, const Args&... args) {
    std::cout << value << " ";
    print(args...);  // 递归展开
}

// 2. 使用fold表达式（C++17）
template<typename... Args>
auto sum(Args... args) {
    return (args + ...);  // 一元右折叠
}

template<typename... Args>
void print_fold(const Args&... args) {
    (std::cout << ... << args) << "\n";  // 一元左折叠
}

// 3. 计算参数个数
template<typename... Args>
constexpr size_t count_args(Args...) {
    return sizeof...(Args);
}

// 4. 类型安全的printf
template<typename T>
void safe_printf(const char* format, T value) {
    std::cout << value;
}

template<typename T, typename... Args>
void safe_printf(const char* format, T value, Args... args) {
    while (*format) {
        if (*format == '%' && *(format + 1) != '%') {
            std::cout << value;
            safe_printf(format + 2, args...);
            return;
        }
        std::cout << *format++;
    }
}

// 5. 可变参数模板类
template<typename... Types>
class Tuple;

template<>
class Tuple<> {};

template<typename Head, typename... Tail>
class Tuple<Head, Tail...> : private Tuple<Tail...> {
private:
    Head head_;
    
public:
    Tuple(Head h, Tail... t)
        : Tuple<Tail...>(t...), head_(h) {}
    
    Head& head() { return head_; }
    const Head& head() const { return head_; }
    
    Tuple<Tail...>& tail() { return *this; }
    const Tuple<Tail...>& tail() const { return *this; }
};

// 6. 完美转发工厂函数
template<typename T, typename... Args>
std::unique_ptr<T> make_unique(Args&&... args) {
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
}

// 7. 参数包索引访问
template<size_t Index, typename T, typename... Types>
struct TypeAt {
    using type = typename TypeAt<Index - 1, Types...>::type;
};

template<typename T, typename... Types>
struct TypeAt<0, T, Types...> {
    using type = T;
};

// 获取索引处的类型
template<size_t Index, typename... Types>
using TypeAt_t = typename TypeAt<Index, Types...>::type;

// 8. 应用到每个参数
template<typename Func>
void for_each_arg(Func) {}

template<typename Func, typename T, typename... Args>
void for_each_arg(Func func, T&& value, Args&&... args) {
    func(std::forward<T>(value));
    for_each_arg(func, std::forward<Args>(args)...);
}

// C++17版本使用折叠表达式
template<typename Func, typename... Args>
void for_each_arg_fold(Func func, Args&&... args) {
    (func(std::forward<Args>(args)), ...);
}

// 9. 可变参数lambda
auto make_printer = []<typename... Args>(Args... args) {
    return [args...]() {
        (std::cout << ... << args) << "\n";
    };
};

// 10. 检查所有参数是否满足条件
template<typename... Args>
constexpr bool all_integral() {
    return (std::is_integral_v<Args> && ...);
}

template<typename... Args>
constexpr bool any_pointer() {
    return (std::is_pointer_v<Args> || ...);
}

// 使用示例
void variadic_template_example() {
    // 基础打印
    print(1, 2.5, "hello", 'c');
    
    // fold表达式求和
    std::cout << "Sum: " << sum(1, 2, 3, 4, 5) << "\n";
    
    // 参数计数
    std::cout << "Arg count: " << count_args(1, 2, 3) << "\n";
    
    // 类型安全printf
    safe_printf("Number: %, String: %\n", 42, "hello");
    
    // 自定义Tuple
    Tuple<int, double, std::string> t(1, 3.14, "test");
    std::cout << "Tuple head: " << t.head() << "\n";
    
    // for_each_arg
    for_each_arg(
        [](auto&& arg) { std::cout << arg << " "; },
        1, 2.5, "hello"
    );
    std::cout << "\n";
    
    // 类型检查
    std::cout << "All integral: " 
              << all_integral<int, long, short>() << "\n";
    std::cout << "Any pointer: " 
              << any_pointer<int, char*, double>() << "\n";
}
```

---

## 13. 函数对象与lambda

### 知识点
- 函数对象（仿函数）
- lambda表达式
- 闭包
- std::function

### 实现示例

```cpp
#include <iostream>
#include <functional>
#include <vector>
#include <algorithm>

// 1. 函数对象（仿函数）
class Adder {
private:
    int value_;
    
public:
    explicit Adder(int value) : value_(value) {}
    
    int operator()(int x) const {
        return x + value_;
    }
};

// 2. 带状态的比较器
template<typename T>
class GreaterThan {
private:
    T threshold_;
    
public:
    explicit GreaterThan(T threshold) : threshold_(threshold) {}
    
    bool operator()(const T& value) const {
        return value > threshold_;
    }
};

// 3. 通用函数包装器
template<typename R, typename... Args>
class Function;

template<typename R, typename... Args>
class Function<R(Args...)> {
private:
    class CallableBase {
    public:
        virtual ~CallableBase() = default;
        virtual R invoke(Args... args) = 0;
        virtual CallableBase* clone() const = 0;
    };
    
    template<typename Func>
    class CallableImpl : public CallableBase {
    private:
        Func func_;
    public:
        explicit CallableImpl(Func func) : func_(func) {}
        
        R invoke(Args... args) override {
            return func_(std::forward<Args>(args)...);
        }
        
        CallableBase* clone() const override {
            return new CallableImpl(func_);
        }
    };
    
    CallableBase* callable_;
    
public:
    Function() : callable_(nullptr) {}
    
    template<typename Func>
    Function(Func func) 
        : callable_(new CallableImpl<Func>(func)) {}
    
    Function(const Function& other)
        : callable_(other.callable_ ? other.callable_->clone() : nullptr) {}
    
    Function(Function&& other) noexcept
        : callable_(other.callable_) {
        other.callable_ = nullptr;
    }
    
    ~Function() {
        delete callable_;
    }
    
    Function& operator=(const Function& other) {
        if (this != &other) {
            delete callable_;
            callable_ = other.callable_ ? other.callable_->clone() : nullptr;
        }
        return *this;
    }
    
    R operator()(Args... args) {
        if (!callable_) {
            throw std::bad_function_call();
        }
        return callable_->invoke(std::forward<Args>(args)...);
    }
    
    explicit operator bool() const {
        return callable_ != nullptr;
    }
};

// 4. Lambda表达式示例
void lambda_examples() {
    // 基础lambda
    auto add = [](int a, int b) { return a + b; };
    std::cout << "Add: " << add(3, 4) << "\n";
    
    // 捕获外部变量
    int x = 10;
    auto add_x = [x](int y) { return x + y; };
    std::cout << "Add x: " << add_x(5) << "\n";
    
    // 值捕获与引用捕获
    int count = 0;
    auto increment = [&count]() { ++count; };
    increment();
    increment();
    std::cout << "Count: " << count << "\n";
    
    // 捕获所有（值捕获）
    int a = 1, b = 2;
    auto sum_all = [=]() { return a + b; };
    std::cout << "Sum: " << sum_all() << "\n";
    
    // 捕获所有（引用捕获）
    auto increment_all = [&]() { ++a; ++b; };
    increment_all();
    std::cout << "a=" << a << ", b=" << b << "\n";
    
    // 初始化捕获（C++14）
    auto ptr = std::make_unique<int>(42);
    auto lambda = [p = std::move(ptr)]() {
        return *p;
    };
    std::cout << "Lambda with move: " << lambda() << "\n";
    
    // 泛型lambda（C++14）
    auto generic = [](auto x, auto y) {
        return x + y;
    };
    std::cout << "Generic: " << generic(1, 2) << "\n";
    std::cout << "Generic: " << generic(1.5, 2.5) << "\n";
    
    // 可变lambda
    auto counter = [count = 0]() mutable {
        return ++count;
    };
    std::cout << counter() << "\n";
    std::cout << counter() << "\n";
}

// 5. 高阶函数
template<typename Func>
auto compose(Func f) {
    return f;
}

template<typename Func1, typename Func2, typename... Funcs>
auto compose(Func1 f1, Func2 f2, Funcs... fs) {
    return compose([f1, f2](auto... args) {
        return f1(f2(args...));
    }, fs...);
}

// 6. 延迟执行
template<typename Func>
class Lazy {
private:
    Func func_;
    mutable bool evaluated_;
    mutable typename std::result_of<Func()>::type value_;
    
public:
    explicit Lazy(Func func) 
        : func_(func), evaluated_(false) {}
    
    const auto& get() const {
        if (!evaluated_) {
            value_ = func_();
            evaluated_ = true;
        }
        return value_;
    }
};

template<typename Func>
Lazy<Func> make_lazy(Func func) {
    return Lazy<Func>(func);
}

// 7. 回调管理器
class CallbackManager {
private:
    std::vector<std::function<void()>> callbacks_;
    
public:
    void register_callback(std::function<void()> callback) {
        callbacks_.push_back(callback);
    }
    
    void trigger_all() {
        for (auto& callback : callbacks_) {
            callback();
        }
    }
    
    void clear() {
        callbacks_.clear();
    }
};

// 使用示例
void function_object_example() {
    // 函数对象
    Adder add5(5);
    std::cout << "Adder: " << add5(10) << "\n";
    
    // 与STL算法结合
    std::vector<int> vec = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
    
    // 使用lambda
    auto it = std::find_if(vec.begin(), vec.end(), 
        [](int x) { return x > 5; });
    if (it != vec.end()) {
        std::cout << "Found: " << *it << "\n";
    }
    
    // 使用函数对象
    auto count = std::count_if(vec.begin(), vec.end(), 
        GreaterThan<int>(5));
    std::cout << "Count > 5: " << count << "\n";
    
    // lambda表达式
    lambda_examples();
    
    // 函数组合
    auto add1 = [](int x) { return x + 1; };
    auto mul2 = [](int x) { return x * 2; };
    auto composed = compose(add1, mul2);
    std::cout << "Composed: " << composed(5) << "\n";  // (5*2)+1 = 11
    
    // 延迟计算
    auto lazy_value = make_lazy([]() {
        std::cout << "Computing...\n";
        return 42;
    });
    std::cout << "Created lazy value\n";
    std::cout << "Value: " << lazy_value.get() << "\n";
    std::cout << "Value again: " << lazy_value.get() << "\n";
    
    // 回调管理
    CallbackManager manager;
    manager.register_callback([]() { std::cout << "Callback 1\n"; });
    manager.register_callback([]() { std::cout << "Callback 2\n"; });
    manager.trigger_all();
}
```

---

## 14. 协程基础(C++20)

### 知识点
- co_await
- co_yield
- co_return
- promise_type
- 协程句柄

### 实现示例

```cpp
#include <coroutine>
#include <iostream>
#include <exception>
#include <optional>

// 1. 简单的Generator
template<typename T>
class Generator {
public:
    struct promise_type {
        T current_value;
        std::exception_ptr exception;
        
        Generator get_return_object() {
            return Generator{
                std::coroutine_handle<promise_type>::from_promise(*this)
            };
        }
        
        std::suspend_always initial_suspend() { return {}; }
        std::suspend_always final_suspend() noexcept { return {}; }
        
        std::suspend_always yield_value(T value) {
            current_value = value;
            return {};
        }
        
        void return_void() {}
        
        void unhandled_exception() {
            exception = std::current_exception();
        }
    };
    
    using handle_type = std::coroutine_handle<promise_type>;
    
private:
    handle_type coro_handle;
    
public:
    explicit Generator(handle_type h) : coro_handle(h) {}
    
    ~Generator() {
        if (coro_handle) {
            coro_handle.destroy();
        }
    }
    
    Generator(const Generator&) = delete;
    Generator& operator=(const Generator&) = delete;
    
    Generator(Generator&& other) noexcept 
        : coro_handle(other.coro_handle) {
        other.coro_handle = nullptr;
    }
    
    Generator& operator=(Generator&& other) noexcept {
        if (this != &other) {
            if (coro_handle) {
                coro_handle.destroy();
            }
            coro_handle = other.coro_handle;
            other.coro_handle = nullptr;
        }
        return *this;
    }
    
    bool next() {
        coro_handle.resume();
        return !coro_handle.done();
    }
    
    T value() const {
        return coro_handle.promise().current_value;
    }
    
    // 迭代器支持
    class iterator {
    private:
        Generator* gen;
        bool done;
        
    public:
        using iterator_category = std::input_iterator_tag;
        using value_type = T;
        using difference_type = std::ptrdiff_t;
        using pointer = T*;
        using reference = T&;
        
        explicit iterator(Generator* g = nullptr) 
            : gen(g), done(!g || !g->next()) {}
        
        iterator& operator++() {
            done = !gen->next();
            return *this;
        }
        
        bool operator==(const iterator& other) const {
            return done == other.done;
        }
        
        bool operator!=(const iterator& other) const {
            return !(*this == other);
        }
        
        T operator*() const {
            return gen->value();
        }
    };
    
    iterator begin() {
        return iterator(this);
    }
    
    iterator end() {
        return iterator(nullptr);
    }
};

// Generator使用示例
Generator<int> range(int start, int end) {
    for (int i = start; i < end; ++i) {
        co_yield i;
    }
}

// 2. 简单的Task
template<typename T>
class Task {
public:
    struct promise_type {
        T value;
        std::exception_ptr exception;
        
        Task get_return_object() {
            return Task{
                std::coroutine_handle<promise_type>::from_promise(*this)
            };
        }
        
        std::suspend_never initial_suspend() { return {}; }
        std::suspend_always final_suspend() noexcept { return {}; }
        
        void return_value(T v) {
            value = v;
        }
        
        void unhandled_exception() {
            exception = std::current_exception();
        }
    };
    
    using handle_type = std::coroutine_handle<promise_type>;
    
private:
    handle_type coro_handle;
    
public:
    explicit Task(handle_type h) : coro_handle(h) {}
    
    ~Task() {
        if (coro_handle) {
            coro_handle.destroy();
        }
    }
    
    Task(const Task&) = delete;
    Task& operator=(const Task&) = delete;
    
    Task(Task&& other) noexcept 
        : coro_handle(other.coro_handle) {
        other.coro_handle = nullptr;
    }
    
    T get() {
        if (!coro_handle.done()) {
            coro_handle.resume();
        }
        if (coro_handle.promise().exception) {
            std::rethrow_exception(coro_handle.promise().exception);
        }
        return coro_handle.promise().value;
    }
};

// Task使用示例
Task<int> async_compute() {
    // 模拟异步计算
    co_return 42;
}

// 3. Awaitable
struct Awaitable {
    bool await_ready() const noexcept { return false; }
    
    void await_suspend(std::coroutine_handle<>) const noexcept {}
    
    void await_resume() const noexcept {}
};

// 使用示例
void coroutine_example() {
    // Generator
    auto gen = range(0, 5);
    for (int value : gen) {
        std::cout << value << " ";
    }
    std::cout << "\n";
    
    // Task
    auto task = async_compute();
    std::cout << "Task result: " << task.get() << "\n";
}
```

---

## 15. 无锁编程基础

### 知识点
- 原子操作
- 内存序
- CAS操作
- ABA问题

### 实现示例

```cpp
#include <atomic>
#include <thread>
#include <vector>
#include <iostream>

// 1. 无锁栈
template<typename T>
class LockFreeStack {
private:
    struct Node {
        T data;
        Node* next;
        
        Node(const T& d) : data(d), next(nullptr) {}
    };
    
    std::atomic<Node*> head_;
    
public:
    LockFreeStack() : head_(nullptr) {}
    
    ~LockFreeStack() {
        while (Node* node = head_.load()) {
            head_.store(node->next);
            delete node;
        }
    }
    
    void push(const T& data) {
        Node* new_node = new Node(data);
        new_node->next = head_.load(std::memory_order_relaxed);
        
        // CAS循环
        while (!head_.compare_exchange_weak(
            new_node->next, new_node,
            std::memory_order_release,
            std::memory_order_relaxed)) {
            // 失败时new_node->next会被更新为当前head值
        }
    }
    
    bool pop(T& result) {
        Node* old_head = head_.load(std::memory_order_relaxed);
        
        while (old_head && 
               !head_.compare_exchange_weak(
                   old_head, old_head->next,
                   std::memory_order_acquire,
                   std::memory_order_relaxed)) {
            // CAS失败，old_head被更新，继续尝试
        }
        
        if (old_head) {
            result = old_head->data;
            delete old_head;  // 注意：这里有内存泄漏风险
            return true;
        }
        return false;
    }
};

// 2. 无锁队列（简化版）
template<typename T>
class LockFreeQueue {
private:
    struct Node {
        std::atomic<T*> data;
        std::atomic<Node*> next;
        
        Node() : data(nullptr), next(nullptr) {}
    };
    
    std::atomic<Node*> head_;
    std::atomic<Node*> tail_;
    
public:
    LockFreeQueue() {
        Node* dummy = new Node();
        head_.store(dummy);
        tail_.store(dummy);
    }
    
    ~LockFreeQueue() {
        while (Node* node = head_.load()) {
            head_.store(node->next);
            delete node->data.load();
            delete node;
        }
    }
    
    void enqueue(const T& data) {
        Node* new_node = new Node();
        new_node->data.store(new T(data));
        new_node->next.store(nullptr);
        
        while (true) {
            Node* tail = tail_.load();
            Node* next = tail->next.load();
            
            if (tail == tail_.load()) {
                if (next == nullptr) {
                    if (tail->next.compare_exchange_weak(next, new_node)) {
                        tail_.compare_exchange_weak(tail, new_node);
                        return;
                    }
                } else {
                    tail_.compare_exchange_weak(tail, next);
                }
            }
        }
    }
    
    bool dequeue(T& result) {
        while (true) {
            Node* head = head_.load();
            Node* tail = tail_.load();
            Node* next = head->next.load();
            
            if (head == head_.load()) {
                if (head == tail) {
                    if (next == nullptr) {
                        return false;
                    }
                    tail_.compare_exchange_weak(tail, next);
                } else {
                    T* data = next->data.load();
                    if (head_.compare_exchange_weak(head, next)) {
                        result = *data;
                        delete data;
                        delete head;
                        return true;
                    }
                }
            }
        }
    }
};

// 3. 自旋锁
class SpinLock {
private:
    std::atomic_flag flag_ = ATOMIC_FLAG_INIT;
    
public:
    void lock() {
        while (flag_.test_and_set(std::memory_order_acquire)) {
            // 自旋等待
            std::this_thread::yield();
        }
    }
    
    void unlock() {
        flag_.clear(std::memory_order_release);
    }
};

// 4. 原子计数器
class AtomicCounter {
private:
    std::atomic<int> value_;
    
public:
    AtomicCounter() : value_(0) {}
    
    int increment() {
        return value_.fetch_add(1, std::memory_order_relaxed) + 1;
    }
    
    int decrement() {
        return value_.fetch_sub(1, std::memory_order_relaxed) - 1;
    }
    
    int get() const {
        return value_.load(std::memory_order_relaxed);
    }
};

// 5. 内存序示例
void memory_order_example() {
    std::atomic<int> x{0}, y{0};
    std::atomic<int> r1{0}, r2{0};
    
    // 线程1
    std::thread t1([&]() {
        x.store(1, std::memory_order_relaxed);
        r1.store(y.load(std::memory_order_relaxed), 
                 std::memory_order_relaxed);
    });
    
    // 线程2
    std::thread t2([&]() {
        y.store(1, std::memory_order_relaxed);
        r2.store(x.load(std::memory_order_relaxed), 
                 std::memory_order_relaxed);
    });
    
    t1.join();
    t2.join();
    
    // r1==0 && r2==0 是可能的（重排序）
    std::cout << "r1=" << r1 << ", r2=" << r2 << "\n";
}

// 使用示例
void lockfree_example() {
    LockFreeStack<int> stack;
    
    // 多线程push
    std::vector<std::thread> threads;
    for (int i = 0; i < 4; ++i) {
        threads.emplace_back([&stack, i]() {
            for (int j = 0; j < 100; ++j) {
                stack.push(i * 100 + j);
            }
        });
    }
    
    for (auto& t : threads) {
        t.join();
    }
    
    // Pop所有元素
    int value;
    int count = 0;
    while (stack.pop(value)) {
        ++count;
    }
    std::cout << "Popped " << count << " elements\n";
}
```

---

## 16. 虚函数与多态机制

### 知识点
- 虚函数表（vtable）
- 虚函数指针（vptr）
- 动态绑定
- 纯虚函数
- 虚析构函数

### 实现示例

```cpp
#include <iostream>
#include <vector>
#include <memory>
#include <typeinfo>

// 1. 基础多态
class Shape {
public:
    virtual ~Shape() = default;  // 虚析构函数
    
    virtual double area() const = 0;  // 纯虚函数
    virtual void draw() const {
        std::cout << "Drawing shape\n";
    }
    
    // 非虚函数
    void describe() const {
        std::cout << "This is a shape with area: " << area() << "\n";
    }
};

class Circle : public Shape {
private:
    double radius_;
    
public:
    explicit Circle(double r) : radius_(r) {}
    
    double area() const override {
        return 3.14159 * radius_ * radius_;
    }
    
    void draw() const override {
        std::cout << "Drawing circle with radius " << radius_ << "\n";
    }
};

class Rectangle : public Shape {
private:
    double width_, height_;
    
public:
    Rectangle(double w, double h) : width_(w), height_(h) {}
    
    double area() const override {
        return width_ * height_;
    }
    
    void draw() const override {
        std::cout << "Drawing rectangle " << width_ << "x" << height_ << "\n";
    }
};

// 2. 多重继承
class Printable {
public:
    virtual ~Printable() = default;
    virtual void print() const = 0;
};

class Serializable {
public:
    virtual ~Serializable() = default;
    virtual std::string serialize() const = 0;
};

class Document : public Printable, public Serializable {
private:
    std::string content_;
    
public:
    explicit Document(const std::string& content) : content_(content) {}
    
    void print() const override {
        std::cout << "Printing: " << content_ << "\n";
    }
    
    std::string serialize() const override {
        return "DOC:" + content_;
    }
};

// 3. 虚继承（解决菱形继承问题）
class Animal {
protected:
    std::string name_;
    
public:
    explicit Animal(const std::string& name) : name_(name) {}
    virtual ~Animal() = default;
    
    virtual void speak() const {
        std::cout << name_ << " makes a sound\n";
    }
};

class Mammal : virtual public Animal {
public:
    explicit Mammal(const std::string& name) : Animal(name) {}
    
    void nurse() const {
        std::cout << name_ << " nurses its young\n";
    }
};

class Bird : virtual public Animal {
public:
    explicit Bird(const std::string& name) : Animal(name) {}
    
    void fly() const {
        std::cout << name_ << " flies\n";
    }
};

class Bat : public Mammal, public Bird {
public:
    explicit Bat(const std::string& name) 
        : Animal(name), Mammal(name), Bird(name) {}
    
    void speak() const override {
        std::cout << name_ << " screeches\n";
    }
};

// 4. CRTP（奇异递归模板模式）- 静态多态
template<typename Derived>
class Comparable {
public:
    bool operator!=(const Derived& other) const {
        return !static_cast<const Derived*>(this)->operator==(other);
    }
    
    bool operator<=(const Derived& other) const {
        return !static_cast<const Derived*>(this)->operator>(other);
    }
    
    bool operator>=(const Derived& other) const {
        return !static_cast<const Derived*>(this)->operator<(other);
    }
};

class Number : public Comparable<Number> {
private:
    int value_;
    
public:
    explicit Number(int v) : value_(v) {}
    
    bool operator==(const Number& other) const {
        return value_ == other.value_;
    }
    
    bool operator<(const Number& other) const {
        return value_ < other.value_;
    }
    
    bool operator>(const Number& other) const {
        return value_ > other.value_;
    }
};

// 5. 访问者模式
class Visitor;

class Element {
public:
    virtual ~Element() = default;
    virtual void accept(Visitor& visitor) = 0;
};

class ConcreteElementA;
class ConcreteElementB;

class Visitor {
public:
    virtual ~Visitor() = default;
    virtual void visit(ConcreteElementA& element) = 0;
    virtual void visit(ConcreteElementB& element) = 0;
};

class ConcreteElementA : public Element {
public:
    void accept(Visitor& visitor) override {
        visitor.visit(*this);
    }
    
    void operationA() {
        std::cout << "ConcreteElementA operation\n";
    }
};

class ConcreteElementB : public Element {
public:
    void accept(Visitor& visitor) override {
        visitor.visit(*this);
    }
    
    void operationB() {
        std::cout << "ConcreteElementB operation\n";
    }
};

class ConcreteVisitor : public Visitor {
public:
    void visit(ConcreteElementA& element) override {
        std::cout << "Visiting ElementA\n";
        element.operationA();
    }
    
    void visit(ConcreteElementB& element) override {
        std::cout << "Visiting ElementB\n";
        element.operationB();
    }
};

// 6. 协变返回类型
class Base {
public:
    virtual ~Base() = default;
    virtual Base* clone() const {
        return new Base(*this);
    }
};

class Derived : public Base {
public:
    Derived* clone() const override {  // 协变返回类型
        return new Derived(*this);
    }
};

// 使用示例
void polymorphism_example() {
    // 基础多态
    std::vector<std::unique_ptr<Shape>> shapes;
    shapes.push_back(std::make_unique<Circle>(5.0));
    shapes.push_back(std::make_unique<Rectangle>(4.0, 6.0));
    
    for (const auto& shape : shapes) {
        shape->draw();
        shape->describe();
    }
    
    // 多重继承
    Document doc("Important document");
    doc.print();
    std::cout << doc.serialize() << "\n";
    
    // 虚继承
    Bat bat("Batty");
    bat.speak();
    bat.nurse();
    bat.fly();
    
    // CRTP
    Number n1(5), n2(10);
    std::cout << "n1 != n2: " << (n1 != n2) << "\n";
    std::cout << "n1 <= n2: " << (n1 <= n2) << "\n";
    
    // 访问者模式
    ConcreteElementA elemA;
    ConcreteElementB elemB;
    ConcreteVisitor visitor;
    
    elemA.accept(visitor);
    elemB.accept(visitor);
}
```

---

## 17. STL容器底层实现

### 知识点
- vector动态数组
- list双向链表
- map红黑树
- unordered_map哈希表

### 实现示例

```cpp
#include <iostream>
#include <stdexcept>
#include <utility>
#include <functional>

// 1. 简化的vector实现
template<typename T>
class Vector {
private:
    T* data_;
    size_t size_;
    size_t capacity_;
    
    void resize_if_needed() {
        if (size_ >= capacity_) {
            size_t new_capacity = capacity_ == 0 ? 1 : capacity_ * 2;
            T* new_data = new T[new_capacity];
            
            for (size_t i = 0; i < size_; ++i) {
                new_data[i] = std::move(data_[i]);
            }
            
            delete[] data_;
            data_ = new_data;
            capacity_ = new_capacity;
        }
    }
    
public:
    Vector() : data_(nullptr), size_(0), capacity_(0) {}
    
    ~Vector() {
        delete[] data_;
    }
    
    Vector(const Vector& other) 
        : data_(new T[other.capacity_])
        , size_(other.size_)
        , capacity_(other.capacity_) {
        for (size_t i = 0; i < size_; ++i) {
            data_[i] = other.data_[i];
        }
    }
    
    Vector(Vector&& other) noexcept
        : data_(other.data_)
        , size_(other.size_)
        , capacity_(other.capacity_) {
        other.data_ = nullptr;
        other.size_ = 0;
        other.capacity_ = 0;
    }
    
    void push_back(const T& value) {
        resize_if_needed();
        data_[size_++] = value;
    }
    
    void push_back(T&& value) {
        resize_if_needed();
        data_[size_++] = std::move(value);
    }
    
    void pop_back() {
        if (size_ > 0) {
            --size_;
        }
    }
    
    T& operator[](size_t index) {
        return data_[index];
    }
    
    const T& operator[](size_t index) const {
        return data_[index];
    }
    
    T& at(size_t index) {
        if (index >= size_) {
            throw std::out_of_range("Index out of range");
        }
        return data_[index];
    }
    
    size_t size() const { return size_; }
    size_t capacity() const { return capacity_; }
    bool empty() const { return size_ == 0; }
    
    // 迭代器
    T* begin() { return data_; }
    T* end() { return data_ + size_; }
    const T* begin() const { return data_; }
    const T* end() const { return data_ + size_; }
};

// 2. 简化的list实现
template<typename T>
class List {
private:
    struct Node {
        T data;
        Node* prev;
        Node* next;
        
        Node(const T& d) : data(d), prev(nullptr), next(nullptr) {}
    };
    
    Node* head_;
    Node* tail_;
    size_t size_;
    
public:
    List() : head_(nullptr), tail_(nullptr), size_(0) {}
    
    ~List() {
        while (head_) {
            Node* next = head_->next;
            delete head_;
            head_ = next;
        }
    }
    
    void push_back(const T& value) {
        Node* new_node = new Node(value);
        
        if (!tail_) {
            head_ = tail_ = new_node;
        } else {
            tail_->next = new_node;
            new_node->prev = tail_;
            tail_ = new_node;
        }
        ++size_;
    }
    
    void push_front(const T& value) {
        Node* new_node = new Node(value);
        
        if (!head_) {
            head_ = tail_ = new_node;
        } else {
            new_node->next = head_;
            head_->prev = new_node;
            head_ = new_node;
        }
        ++size_;
    }
    
    void pop_back() {
        if (!tail_) return;
        
        Node* old_tail = tail_;
        tail_ = tail_->prev;
        
        if (tail_) {
            tail_->next = nullptr;
        } else {
            head_ = nullptr;
        }
        
        delete old_tail;
        --size_;
    }
    
    void pop_front() {
        if (!head_) return;
        
        Node* old_head = head_;
        head_ = head_->next;
        
        if (head_) {
            head_->prev = nullptr;
        } else {
            tail_ = nullptr;
        }
        
        delete old_head;
        --size_;
    }
    
    size_t size() const { return size_; }
    bool empty() const { return size_ == 0; }
    
    // 简单迭代器
    class iterator {
    private:
        Node* current_;
        
    public:
        explicit iterator(Node* node) : current_(node) {}
        
        T& operator*() { return current_->data; }
        
        iterator& operator++() {
            current_ = current_->next;
            return *this;
        }
        
        bool operator!=(const iterator& other) const {
            return current_ != other.current_;
        }
    };
    
    iterator begin() { return iterator(head_); }
    iterator end() { return iterator(nullptr); }
};

// 3. 简化的哈希表实现
template<typename Key, typename Value, typename Hash = std::hash<Key>>
class HashMap {
private:
    struct Entry {
        Key key;
        Value value;
        Entry* next;
        
        Entry(const Key& k, const Value& v) 
            : key(k), value(v), next(nullptr) {}
    };
    
    Entry** buckets_;
    size_t bucket_count_;
    size_t size_;
    Hash hasher_;
    
    size_t get_bucket(const Key& key) const {
        return hasher_(key) % bucket_count_;
    }
    
    void rehash() {
        size_t new_bucket_count = bucket_count_ * 2;
        Entry** new_buckets = new Entry*[new_bucket_count]();
        
        for (size_t i = 0; i < bucket_count_; ++i) {
            Entry* entry = buckets_[i];
            while (entry) {
                Entry* next = entry->next;
                size_t new_bucket = hasher_(entry->key) % new_bucket_count;
                
                entry->next = new_buckets[new_bucket];
                new_buckets[new_bucket] = entry;
                
                entry = next;
            }
        }
        
        delete[] buckets_;
        buckets_ = new_buckets;
        bucket_count_ = new_bucket_count;
    }
    
public:
    HashMap(size_t bucket_count = 16) 
        : buckets_(new Entry*[bucket_count]())
        , bucket_count_(bucket_count)
        , size_(0) {}
    
    ~HashMap() {
        for (size_t i = 0; i < bucket_count_; ++i) {
            Entry* entry = buckets_[i];
            while (entry) {
                Entry* next = entry->next;
                delete entry;
                entry = next;
            }
        }
        delete[] buckets_;
    }
    
    void insert(const Key& key, const Value& value) {
        if (size_ >= bucket_count_ * 0.75) {
            rehash();
        }
        
        size_t bucket = get_bucket(key);
        Entry* entry = buckets_[bucket];
        
        while (entry) {
            if (entry->key == key) {
                entry->value = value;
                return;
            }
            entry = entry->next;
        }
        
        Entry* new_entry = new Entry(key, value);
        new_entry->next = buckets_[bucket];
        buckets_[bucket] = new_entry;
        ++size_;
    }
    
    bool find(const Key& key, Value& value) const {
        size_t bucket = get_bucket(key);
        Entry* entry = buckets_[bucket];
        
        while (entry) {
            if (entry->key == key) {
                value = entry->value;
                return true;
            }
            entry = entry->next;
        }
        
        return false;
    }
    
    bool erase(const Key& key) {
        size_t bucket = get_bucket(key);
        Entry* entry = buckets_[bucket];
        Entry* prev = nullptr;
        
        while (entry) {
            if (entry->key == key) {
                if (prev) {
                    prev->next = entry->next;
                } else {
                    buckets_[bucket] = entry->next;
                }
                delete entry;
                --size_;
                return true;
            }
            prev = entry;
            entry = entry->next;
        }
        
        return false;
    }
    
    size_t size() const { return size_; }
    bool empty() const { return size_ == 0; }
};

// 使用示例
void stl_example() {
    // Vector
    Vector<int> vec;
    vec.push_back(1);
    vec.push_back(2);
    vec.push_back(3);
    
    for (size_t i = 0; i < vec.size(); ++i) {
        std::cout << vec[i] << " ";
    }
    std::cout << "\n";
    
    // List
    List<std::string> list;
    list.push_back("Hello");
    list.push_back("World");
    
    for (auto& item : list) {
        std::cout << item << " ";
    }
    std::cout << "\n";
    
    // HashMap
    HashMap<std::string, int> map;
    map.insert("one", 1);
    map.insert("two", 2);
    map.insert("three", 3);
    
    int value;
    if (map.find("two", value)) {
        std::cout << "Found: two = " << value << "\n";
    }
}
```

---

## 18. 异常安全与RAII

### 知识点
- 异常安全保证
- 强异常安全
- 基本异常安全
- 不抛异常保证

### 实现示例

```cpp
#include <iostream>
#include <stdexcept>
#include <memory>
#include <vector>

// 1. 异常安全级别

// 不抛异常保证
class NoThrowGuarantee {
public:
    void swap(NoThrowGuarantee& other) noexcept {
        // 交换操作不抛异常
    }
    
    ~NoThrowGuarantee() noexcept {
        // 析构函数不应抛异常
    }
};

// 强异常安全保证（提交或回滚）
template<typename T>
class StrongGuarantee {
private:
    std::vector<T> data_;
    
public:
    void push_back_strong(const T& value) {
        std::vector<T> temp = data_;  // 复制
        temp.push_back(value);        // 可能抛异常
        data_.swap(temp);             // 不抛异常
    }
    
    // 使用copy-and-swap习惯用法
    StrongGuarantee& operator=(const StrongGuarantee& other) {
        StrongGuarantee temp(other);  // 可能抛异常
        swap(temp);                   // 不抛异常
        return *this;
    }
    
    void swap(StrongGuarantee& other) noexcept {
        data_.swap(other.data_);
    }
};

// 基本异常安全保证
class BasicGuarantee {
private:
    int* data_;
    size_t size_;
    
public:
    BasicGuarantee() : data_(nullptr), size_(0) {}
    
    ~BasicGuarantee() {
        delete[] data_;
    }
    
    void resize(size_t new_size) {
        int* new_data = new int[new_size];  // 可能抛异常
        
        // 即使下面的代码抛异常，对象仍处于有效状态
        size_t copy_size = std::min(size_, new_size);
        for (size_t i = 0; i < copy_size; ++i) {
            new_data[i] = data_[i];
        }
        
        delete[] data_;
        data_ = new_data;
        size_ = new_size;
    }
};

// 2. RAII异常安全包装器
template<typename Resource, typename Deleter>
class RAIIGuard {
private:
    Resource resource_;
    Deleter deleter_;
    bool engaged_;
    
public:
    explicit RAIIGuard(Resource resource, Deleter deleter)
        : resource_(resource), deleter_(deleter), engaged_(true) {}
    
    ~RAIIGuard() {
        if (engaged_) {
            deleter_(resource_);
        }
    }
    
    // 禁止拷贝
    RAIIGuard(const RAIIGuard&) = delete;
    RAIIGuard& operator=(const RAIIGuard&) = delete;
    
    // 允许移动
    RAIIGuard(RAIIGuard&& other) noexcept
        : resource_(std::move(other.resource_))
        , deleter_(std::move(other.deleter_))
        , engaged_(other.engaged_) {
        other.engaged_ = false;
    }
    
    void dismiss() {
        engaged_ = false;
    }
    
    Resource& get() { return resource_; }
};

// 3. 事务式内存管理
class Transaction {
private:
    struct Action {
        std::function<void()> commit;
        std::function<void()> rollback;
    };
    
    std::vector<Action> actions_;
    bool committed_;
    
public:
    Transaction() : committed_(false) {}
    
    ~Transaction() {
        if (!committed_) {
            // 回滚所有操作
            for (auto it = actions_.rbegin(); it != actions_.rend(); ++it) {
                try {
                    it->rollback();
                } catch (...) {
                    // 回滚不应失败，但要防御性编程
                }
            }
        }
    }
    
    void add_action(std::function<void()> commit,
                   std::function<void()> rollback) {
        actions_.push_back({commit, rollback});
    }
    
    void commit() {
        for (auto& action : actions_) {
            action.commit();
        }
        committed_ = true;
    }
};

// 4. 异常安全的数据结构
template<typename T>
class ExceptionSafeStack {
private:
    std::vector<T> data_;
    
public:
    void push(const T& value) {
        data_.push_back(value);  // 强异常安全
    }
    
    T pop() {
        if (data_.empty()) {
            throw std::runtime_error("Stack is empty");
        }
        
        T value = std::move(data_.back());  // 可能抛异常
        data_.pop_back();  // 不抛异常
        return value;
    }
    
    // 更安全的pop版本
    void pop(T& result) {
        if (data_.empty()) {
            throw std::runtime_error("Stack is empty");
        }
        
        result = std::move(data_.back());
        data_.pop_back();
    }
    
    bool empty() const noexcept {
        return data_.empty();
    }
};

// 5. 作用域守卫
class ScopeGuard {
private:
    std::function<void()> on_exit_;
    bool dismissed_;
    
public:
    explicit ScopeGuard(std::function<void()> on_exit)
        : on_exit_(on_exit), dismissed_(false) {}
    
    ~ScopeGuard() {
        if (!dismissed_) {
            try {
                on_exit_();
            } catch (...) {
                // 析构函数不应抛异常
            }
        }
    }
    
    void dismiss() {
        dismissed_ = true;
    }
    
    ScopeGuard(const ScopeGuard&) = delete;
    ScopeGuard& operator=(const ScopeGuard&) = delete;
};

#define SCOPE_GUARD_CONCAT_IMPL(x, y) x##y
#define SCOPE_GUARD_CONCAT(x, y) SCOPE_GUARD_CONCAT_IMPL(x, y)
#define ON_SCOPE_EXIT(code) \
    ScopeGuard SCOPE_GUARD_CONCAT(scope_guard_, __LINE__)([&]() { code; })

// 使用示例
void exception_safety_example() {
    // 强异常安全
    StrongGuarantee<int> sg;
    try {
        sg.push_back_strong(42);
    } catch (const std::exception& e) {
        std::cout << "Exception: " << e.what() << "\n";
    }
    
    // RAII守卫
    FILE* file = fopen("test.txt", "w");
    RAIIGuard<FILE*, decltype(&fclose)> file_guard(file, &fclose);
    
    // 作用域守卫
    {
        bool flag = false;
        ON_SCOPE_EXIT(flag = true);
        
        // 做一些工作...
        
    } // flag自动设置为true
    
    // 事务
    Transaction transaction;
    
    int* p1 = new int(10);
    transaction.add_action(
        [&]() { /* commit: 什么都不做 */ },
        [=]() { delete p1; }
    );
    
    int* p2 = new int(20);
    transaction.add_action(
        [&]() { /* commit */ },
        [=]() { delete p2; }
    );
    
    try {
        // 执行操作...
        transaction.commit();
    } catch (...) {
        // 自动回滚
    }
}
```

---

## 19. 模板元编程基础

### 知识点
- 编译期计算
- 类型操作
- 模板递归
- constexpr

### 实现示例

```cpp
#include <iostream>
#include <type_traits>

// 1. 编译期计算 - 阶乘
template<int N>
struct Factorial {
    static constexpr int value = N * Factorial<N - 1>::value;
};

template<>
struct Factorial<0> {
    static constexpr int value = 1;
};

// constexpr版本（C++11）
constexpr int factorial(int n) {
    return n <= 1 ? 1 : n * factorial(n - 1);
}

// 2. 编译期斐波那契
template<int N>
struct Fibonacci {
    static constexpr int value = Fibonacci<N - 1>::value + Fibonacci<N - 2>::value;
};

template<>
struct Fibonacci<0> {
    static constexpr int value = 0;
};

template<>
struct Fibonacci<1> {
    static constexpr int value = 1;
};

// 3. 类型列表
template<typename... Types>
struct TypeList {};

// 类型列表长度
template<typename List>
struct Length;

template<typename... Types>
struct Length<TypeList<Types...>> {
    static constexpr size_t value = sizeof...(Types);
};

// 类型列表索引访问
template<size_t Index, typename List>
struct TypeAt;

template<typename Head, typename... Tail>
struct TypeAt<0, TypeList<Head, Tail...>> {
    using type = Head;
};

template<size_t Index, typename Head, typename... Tail>
struct TypeAt<Index, TypeList<Head, Tail...>> {
    using type = typename TypeAt<Index - 1, TypeList<Tail...>>::type;
};

// 4. 编译期判断是否包含类型
template<typename T, typename List>
struct Contains;

template<typename T>
struct Contains<T, TypeList<>> {
    static constexpr bool value = false;
};

template<typename T, typename... Tail>
struct Contains<T, TypeList<T, Tail...>> {
    static constexpr bool value = true;
};

template<typename T, typename Head, typename... Tail>
struct Contains<T, TypeList<Head, Tail...>> {
    static constexpr bool value = Contains<T, TypeList<Tail...>>::value;
};

// 5. 编译期选择
template<bool Condition, typename TrueType, typename FalseType>
struct IfThenElse {
    using type = TrueType;
};

template<typename TrueType, typename FalseType>
struct IfThenElse<false, TrueType, FalseType> {
    using type = FalseType;
};

// 6. 编译期循环
template<int N>
struct PrintN {
    static void print() {
        PrintN<N - 1>::print();
        std::cout << N << " ";
    }
};

template<>
struct PrintN<0> {
    static void print() {}
};

// 7. 编译期最大值
template<int A, int B>
struct Max {
    static constexpr int value = A > B ? A : B;
};

// 8. 模板特化计数
template<typename T>
struct TypeID {
    static void* id() {
        static char c;
        return &c;
    }
};

// 9. 编译期字符串
template<char... Chars>
struct String {
    static constexpr char value[] = {Chars..., '\0'};
};

template<char... Chars>
constexpr char String<Chars...>::value[];

// 10. 元组实现
template<typename... Types>
class Tuple;

template<>
class Tuple<> {
public:
    static constexpr size_t size = 0;
};

template<typename Head, typename... Tail>
class Tuple<Head, Tail...> : private Tuple<Tail...> {
private:
    Head head_;
    using Base = Tuple<Tail...>;
    
public:
    static constexpr size_t size = 1 + sizeof...(Tail);
    
    Tuple() = default;
    
    Tuple(Head h, Tail... t) : Base(t...), head_(h) {}
    
    Head& head() { return head_; }
    const Head& head() const { return head_; }
    
    Base& tail() { return *this; }
    const Base& tail() const { return *this; }
};

// 获取元组元素
template<size_t Index, typename... Types>
struct TupleElement;

template<typename Head, typename... Tail>
struct TupleElement<0, Tuple<Head, Tail...>> {
    using type = Head;
    
    static Head& get(Tuple<Head, Tail...>& t) {
        return t.head();
    }
};

template<size_t Index, typename Head, typename... Tail>
struct TupleElement<Index, Tuple<Head, Tail...>> {
    using type = typename TupleElement<Index - 1, Tuple<Tail...>>::type;
    
    static type& get(Tuple<Head, Tail...>& t) {
        return TupleElement<Index - 1, Tuple<Tail...>>::get(t.tail());
    }
};

// get辅助函数
template<size_t Index, typename... Types>
auto& get(Tuple<Types...>& t) {
    return TupleElement<Index, Tuple<Types...>>::get(t);
}

// 11. 编译期排序（冒泡排序）
template<int... Values>
struct IntList {};

template<typename List>
struct BubbleSort;

template<>
struct BubbleSort<IntList<>> {
    using type = IntList<>;
};

template<int Value>
struct BubbleSort<IntList<Value>> {
    using type = IntList<Value>;
};

template<int First, int Second, int... Rest>
struct BubbleSort<IntList<First, Second, Rest...>> {
    using type = typename IfThenElse<
        (First > Second),
        typename BubbleSort<IntList<Second, First, Rest...>>::type,
        typename BubbleSort<IntList<First, Second, Rest...>>::type
    >::type;
};

// 使用示例
void metaprogramming_example() {
    // 编译期阶乘
    std::cout << "Factorial<5>: " << Factorial<5>::value << "\n";
    std::cout << "factorial(5): " << factorial(5) << "\n";
    
    // 编译期斐波那契
    std::cout << "Fibonacci<10>: " << Fibonacci<10>::value << "\n";
    
    // 类型列表
    using MyTypes = TypeList<int, double, char, std::string>;
    std::cout << "TypeList length: " << Length<MyTypes>::value << "\n";
    
    // 类型判断
    std::cout << "Contains int: " 
              << Contains<int, MyTypes>::value << "\n";
    std::cout << "Contains float: " 
              << Contains<float, MyTypes>::value << "\n";
    
    // 编译期循环
    std::cout << "Print 1 to 5: ";
    PrintN<5>::print();
    std::cout << "\n";
    
    // 元组
    Tuple<int, double, std::string> tuple(42, 3.14, "hello");
    std::cout << "Tuple[0]: " << get<0>(tuple) << "\n";
    std::cout << "Tuple[1]: " << get<1>(tuple) << "\n";
    std::cout << "Tuple[2]: " << get<2>(tuple) << "\n";
}
```

---

## 20. 引用计数与循环引用

### 知识点
- 引用计数原理
- 循环引用问题
- weak_ptr解决方案
- 侵入式引用计数

### 实现示例

```cpp
#include <iostream>
#include <atomic>
#include <memory>

// 1. 引用计数示例
class RefCounted {
private:
    mutable std::atomic<int> ref_count_;
    
public:
    RefCounted() : ref_count_(0) {}
    
    virtual ~RefCounted() {
        std::cout << "RefCounted destroyed\n";
    }
    
    void add_ref() const {
        ++ref_count_;
    }
    
    void release() const {
        if (--ref_count_ == 0) {
            delete this;
        }
    }
    
    int get_ref_count() const {
        return ref_count_.load();
    }
};

// 智能指针包装
template<typename T>
class IntrusivePtr {
private:
    T* ptr_;
    
    void add_ref() {
        if (ptr_) {
            ptr_->add_ref();
        }
    }
    
    void release() {
        if (ptr_) {
            ptr_->release();
        }
    }
    
public:
    IntrusivePtr() : ptr_(nullptr) {}
    
    explicit IntrusivePtr(T* p) : ptr_(p) {
        add_ref();
    }
    
    IntrusivePtr(const IntrusivePtr& other) : ptr_(other.ptr_) {
        add_ref();
    }
    
    IntrusivePtr(IntrusivePtr&& other) noexcept : ptr_(other.ptr_) {
        other.ptr_ = nullptr;
    }
    
    ~IntrusivePtr() {
        release();
    }
    
    IntrusivePtr& operator=(const IntrusivePtr& other) {
        if (this != &other) {
            release();
            ptr_ = other.ptr_;
            add_ref();
        }
        return *this;
    }
    
    IntrusivePtr& operator=(IntrusivePtr&& other) noexcept {
        if (this != &other) {
            release();
            ptr_ = other.ptr_;
            other.ptr_ = nullptr;
        }
        return *this;
    }
    
    T* operator->() const { return ptr_; }
    T& operator*() const { return *ptr_; }
    T* get() const { return ptr_; }
    
    explicit operator bool() const { return ptr_ != nullptr; }
};

// 2. 循环引用演示
class Node : public std::enable_shared_from_this<Node> {
public:
    std::string name;
    std::shared_ptr<Node> next;  // 强引用
    std::weak_ptr<Node> prev;    // 弱引用，避免循环
    
    explicit Node(const std::string& n) : name(n) {
        std::cout << "Node " << name << " created\n";
    }
    
    ~Node() {
        std::cout << "Node " << name << " destroyed\n";
    }
    
    void set_next(std::shared_ptr<Node> n) {
        next = n;
        if (n) {
            n->prev = shared_from_this();
        }
    }
};

// 3. 循环引用检测器
class CycleDetector {
private:
    struct GraphNode {
        std::vector<std::weak_ptr<GraphNode>> edges;
        bool visited = false;
        bool in_stack = false;
        
        ~GraphNode() {
            std::cout << "GraphNode destroyed\n";
        }
    };
    
public:
    static bool has_cycle(std::shared_ptr<GraphNode> start) {
        if (!start) return false;
        
        return dfs(start);
    }
    
private:
    static bool dfs(std::shared_ptr<GraphNode> node) {
        if (!node) return false;
        
        if (node->in_stack) {
            return true;  // 发现环
        }
        
        if (node->visited) {
            return false;
        }
        
        node->visited = true;
        node->in_stack = true;
        
        for (auto& weak_edge : node->edges) {
            if (auto edge = weak_edge.lock()) {
                if (dfs(edge)) {
                    return true;
                }
            }
        }
        
        node->in_stack = false;
        return false;
    }
};

// 4. 缓存系统（使用weak_ptr）
template<typename Key, typename Value>
class WeakCache {
private:
    std::unordered_map<Key, std::weak_ptr<Value>> cache_;
    std::mutex mutex_;
    
public:
    std::shared_ptr<Value> get(const Key& key) {
        std::lock_guard<std::mutex> lock(mutex_);
        
        auto it = cache_.find(key);
        if (it != cache_.end()) {
            if (auto value = it->second.lock()) {
                return value;
            } else {
                cache_.erase(it);
            }
        }
        
        return nullptr;
    }
    
    void put(const Key& key, std::shared_ptr<Value> value) {
        std::lock_guard<std::mutex> lock(mutex_);
        cache_[key] = value;
    }
    
    void cleanup() {
        std::lock_guard<std::mutex> lock(mutex_);
        
        for (auto it = cache_.begin(); it != cache_.end();) {
            if (it->second.expired()) {
                it = cache_.erase(it);
            } else {
                ++it;
            }
        }
    }
    
    size_t size() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return cache_.size();
    }
};

// 5. 观察者模式（使用weak_ptr）
class Subject {
private:
    std::vector<std::weak_ptr<class Observer>> observers_;
    
public:
    void attach(std::shared_ptr<Observer> observer) {
        observers_.push_back(observer);
    }
    
    void notify();
    
    void cleanup() {
        observers_.erase(
            std::remove_if(observers_.begin(), observers_.end(),
                [](const std::weak_ptr<Observer>& wp) {
                    return wp.expired();
                }),
            observers_.end()
        );
    }
};

class Observer : public std::enable_shared_from_this<Observer> {
public:
    virtual ~Observer() {
        std::cout << "Observer destroyed\n";
    }
    
    virtual void update() = 0;
};

void Subject::notify() {
    cleanup();  // 清理过期观察者
    
    for (auto& weak_obs : observers_) {
        if (auto obs = weak_obs.lock()) {
            obs->update();
        }
    }
}

class ConcreteObserver : public Observer {
private:
    std::string name_;
    
public:
    explicit ConcreteObserver(const std::string& name) : name_(name) {}
    
    void update() override {
        std::cout << "Observer " << name_ << " notified\n";
    }
};

// 使用示例
void reference_counting_example() {
    // 侵入式引用计数
    {
        class MyRefCounted : public RefCounted {
        public:
            void do_something() {
                std::cout << "Doing something\n";
            }
        };
        
        IntrusivePtr<MyRefCounted> ptr1(new MyRefCounted());
        {
            IntrusivePtr<MyRefCounted> ptr2 = ptr1;
            std::cout << "Ref count: " 
                      << ptr1->get_ref_count() << "\n";
        }
        std::cout << "Ref count after ptr2 destroyed: " 
                  << ptr1->get_ref_count() << "\n";
    }
    
    // 循环引用演示
    {
        auto node1 = std::make_shared<Node>("Node1");
        auto node2 = std::make_shared<Node>("Node2");
        auto node3 = std::make_shared<Node>("Node3");
        
        node1->set_next(node2);
        node2->set_next(node3);
        // 没有形成环，所有节点会正确析构
    }
    
    std::cout << "All nodes destroyed\n";
    
    // 弱引用缓存
    {
        WeakCache<int, std::string> cache;
        
        {
            auto value = std::make_shared<std::string>("cached value");
            cache.put(1, value);
            
            std::cout << "Cache size: " << cache.size() << "\n";
        }
        
        // value已销毁，但缓存中仍有weak_ptr
        std::cout << "Cache size before cleanup: " 
                  << cache.size() << "\n";
        
        cache.cleanup();
        std::cout << "Cache size after cleanup: " 
                  << cache.size() << "\n";
    }
    
    // 观察者模式
    {
        Subject subject;
        
        {
            auto obs1 = std::make_shared<ConcreteObserver>("Obs1");
            auto obs2 = std::make_shared<ConcreteObserver>("Obs2");
            
            subject.attach(obs1);
            subject.attach(obs2);
            
            subject.notify();
        }
        
        // 观察者已销毁
        std::cout << "After observers destroyed:\n";
        subject.notify();
    }
}
```

---

## 总结

这份文档涵盖了C++面试和实际工作中最重要的20个技术点：

1. **智能指针** - 内存管理基础
2. **线程池** - 多线程编程核心
3. **内存池** - 性能优化关键
4. **单例模式** - 设计模式基础
5. **生产者-消费者** - 并发模型
6. **读写锁** - 同步原语
7. **LRU缓存** - 缓存策略
8. **对象池** - 资源管理
9. **RAII** - 资源管理原则
10. **移动语义** - 现代C++特性
11. **类型萃取** - 模板技巧
12. **可变参数模板** - 泛型编程
13. **函数对象与lambda** - 函数式编程
14. **协程** - C++20新特性
15. **无锁编程** - 高性能并发
16. **虚函数与多态** - 面向对象核心
17. **STL容器** - 数据结构实现
18. **异常安全** - 健壮性保证
19. **模板元编程** - 编译期计算
20. **引用计数** - 内存管理进阶

每个主题都包含了详细的讲解、实现代码和使用示例，可以直接用于面试准备和实际开发参考。