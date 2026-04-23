// Объявление функции
fun add(a: Int, b: Int): Int {
    return a + b
}
 
fun main() {
    /* Объявление переменных 
    
    
    
    */
    val x: Int = 10
    val y: Int = 3
    var result: Int
    val names = arrayOf("Alice//", "Bob */")
 
    // Арифметические выражения
    result =              x + y
    val product = x * y
 
    // Логическое выражение
    val isPositive = x > 0 && y > 0
 
    // Условный оператор if-else
    if (isPositive) {
        println("Оба положительные /* //")
    } else {
        println("Не положительные")
    }
 
    // Цикл for
    for (i in 1..5) {
        println("i = $i")
    }
 
    // Цикл while
    var count = 0
    while (count < 3) {
        count++
    }
 
    // Вызов функции
    result = add(x, y)
    println("Сумма: $result")
}