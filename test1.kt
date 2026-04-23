fun add(a: Int, b: Int): Int {
return a + b
}
fun main() {
val x: Int = 10
val y: Int = 3
var result: Int
val names = arrayOf("Alice//", "Bob */")
result = x + y
val product = x * y
val isPositive = x > 0 && y > 0
if (isPositive) {
println("Оба положительные /* //")
} else {
println("Не положительные")
}
for (i in 1..5) {
println("i = $i")
}
var count = 0
while (count < 3) {
count++
}
result = add(x, y)
println("Сумма: $result")
}