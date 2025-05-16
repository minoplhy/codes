#include <stdio.h>
#include <stdlib.h>

// This is rewrite of 'running_number' with help from ghidra
// while ensuring the integrity of program flows and so on

int main(void) {
    int seed;
    int rand_var;
    int i;
    int md5_answer;
    
    printf("Time: ");
    scanf("%u", &seed);
    srand(seed);

    long sum = 0;

    for (i = 0xa07; i > 0x7e7; i--) { // 2567 2023
        if (i % 3 != 0) {
            rand_var = rand();
            sum = sum + rand_var;
        }
    }

    if (sum == 0x5aad48bfa6) { // 389454282662
        printf("THCTT24{");
        for (i = 10; i < 0x4a; i++) { // 74
            if ((i & 1) == 0) {
                rand_var = rand();
                md5_answer = rand_var % 0x10;
                printf("%x", md5_answer); // 16
            }
        }
    puts("}");
    } else {
        puts("No Flag");
    }
}