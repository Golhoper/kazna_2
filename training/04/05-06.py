# один элемент можно добавить в список через метод append (в конец списка)
# несколько элементов можно добавить в список через extend (в конец списка)
# удалить какой-то элемент из списка можно методом del

numbers = []

num = [4, 5, 6]

numbers.append(1)
numbers.append(2)
numbers.append(3)
numbers.extend(num)
del numbers[-2]

print(numbers)