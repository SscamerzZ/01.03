#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_NAME_LEN 50
#define MAX_COMPONENTS 100

typedef struct {
    int id;
    char name[MAX_NAME_LEN];
} Component;

void readComponentsFromFile(const char *filename, Component components[], int *count) {
    FILE *file = fopen(filename, "r");
    if (!file) {
        printf("Ошибка при открытии файла.\n");
        exit(1);
    }

    *count = 0;
    while (fscanf(file, "%d %s", &components[*count].id, components[*count].name) != EOF) {
        (*count)++;
    }

    fclose(file);
}

void addComponentsFromConsole(Component components[], int *count) {
    int num;
    printf("Сколько комплектующих вы хотите добавить? ");
    scanf("%d", &num);

    for (int i = 0; i < num; i++) {
        printf("Введите ID и название комплектующего (через пробел): ");
        scanf("%d %s", &components[*count].id, components[*count].name);
        (*count)++;
    }
}

void printTable(Component components[], int count) {
    printf("Комплект:\n");
    for (int i = 0; i < count; i++) {
        printf("%d -- %s\n", components[i].id, components[i].name);
    }
}

int main() {
    Component components[MAX_COMPONENTS];
    int count = 0;

    int choice;

    do {
        printf("Выберите действие:\n");
        printf("1. Загрузить комплектующие из файла\n");
        printf("2. Добавить комплектующие вручную\n");
        printf("3. Показать комплектующие\n");
        printf("0. Выйти\n");
        printf("Ваш выбор: ");
        scanf("%d", &choice);

        switch (choice) {
            case 1:
                readComponentsFromFile("components.txt", components, &count);
                printf("Данные из файла загружены.\n");
                break;
            case 2:
                addComponentsFromConsole(components, &count);
                break;
            case 3:
                printTable(components, count);
                break;
            case 0:
                printf("Выход из программы.\n");
                break;
            default:
                printf("Неверный выбор! Попробуйте снова.\n");
                break;
        }
    } while (choice != 0);

    return 0;
}