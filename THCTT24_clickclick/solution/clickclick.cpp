#include <cstdint>
#include <cstdio>
#include <string>

std::string secret = "29648872964875296486429648872964887296497729649832964920296497929649762964903296497829649772964983296489829649832964903296498729649822964986296498229649862964983296497629649792964987296498029649872964982296498029649822964979296498229649832964979296497929649782964983296489629649812964926";
int32_t key = 2964931;
int32_t chunk_size = std::to_string(key).length();

std::string flag_chars = {};

int main() {
    for (int i=0; i < secret.length(); i += chunk_size) {
        std::string chunk = secret.substr(i, chunk_size);
        int encoded = std::stoi(chunk);
        char decoded_char = static_cast<char>(encoded ^ key);
        flag_chars += decoded_char;   
    }
    printf("%s\n", flag_chars.c_str());
}