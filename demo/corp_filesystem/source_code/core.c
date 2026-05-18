#include <stdio.h>

int compute_checksum(const char *data, int len) {
    int sum = 0;
    for (int i = 0; i < len; i++) sum += (unsigned char)data[i];
    return sum;
}
