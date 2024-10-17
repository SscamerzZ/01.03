#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_RECORDS 100

struct Record {
    char date[11];
    char group[20];
    char name[50];
    int absences;
};

int compare(const void *a, const void *b) {
    const struct Record *recA = a;
    const struct Record *recB = b;
    
    if (recA->absences != recB->absences)
        return recB->absences - recA->absences;
    if (strcmp(recA->date, recB->date) != 0)
        return strcmp(recA->date, recB->date);
    if (strcmp(recA->group, recB->group) != 0)
        return strcmp(recA->group, recB->group);
    return strcmp(recA->name, recB->name);
}

int main() {
    struct Record records[MAX_RECORDS];
    int count = 0;

    FILE *file = fopen("students.txt", "r");
    if (!file) {
        return 0; 
    }

    while (count < MAX_RECORDS && fscanf(file, "%10s %19s %49s %d", records[count].date, records[count].group, records[count].name, &records[count].absences) == 4) {
        count++;
    }

    fclose(file);
    qsort(records, count, sizeof(struct Record), compare);

    printf("Пропуски:\n");
    for (int i = 0; i < count; i++) {
        printf("%s %s %s %d\n", records[i].date, records[i].group, records[i].name, records[i].absences);
    }

    return 0;
}