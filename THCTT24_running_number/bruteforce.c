#include <stdio.h>
#include <stdlib.h>

// This is da bruteforce code to get the right random seed

int main(void) {
    int seed;
    long sum;
    int rand_var;
    int i;
    int md5_answer;
    
    for (seed = 0; seed <= 1000000000;seed++) {
        srand(seed);
        sum = 0;
        for (i = 0xa07; i > 0x7e7; i--) { // 2567 2023
            if (i % 3 != 0) {
                rand_var = rand();
                sum = sum + rand_var;
            }
        }
        printf("%u\n", seed);

        if (sum == 0x5aad48bfa6) { // 389454282662
            printf("THCTT24{");
            for (i = 10; i < 0x4a; i++) { // 74
                if ((i & 1) == 0) {
                    rand_var = rand();
                    md5_answer = rand_var % 0x10; // 16
                    printf("%x", md5_answer);
                }
            }
            puts("}\n");
            printf("Seed -> %d\n", seed);
            break;
        }
    }
}