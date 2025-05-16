#include <stdint.h>
#include <stdio.h>
#include <string.h>

char secret[] = "29648872964875296486429648872964887296497729649832964920296497929649762964903296497829649772964983296489829649832964903296498729649822964986296498229649862964983296497629649792964987296498029649872964982296498029649822964979296498229649832964979296497929649782964983296489629649812964926";
int32_t key = 2964931; // 7
char key_string[0x20]; // assigned a sustainable amount of space lmao

char flag[0x99]; // assigned a sustainable amount of space lmao
int flag_index = 0;

int main() {
    int32_t chunk_size;
    sprintf(key_string, "%d", key); // convert int->char[0x20] to get a chunk_size
    chunk_size = strlen(key_string);
    char chunk[chunk_size];

    for (int i=0; i < strlen(secret); i += chunk_size) {
        strncpy(chunk, secret + i, chunk_size);
        int encoded;
        sscanf(chunk, "%d", &encoded);
        char decoded = (char)(encoded ^ key);
        flag[flag_index++] += decoded; // char index in SEE lang regards
    }
    printf("%s\n", flag);
}