#define ADDR_MASK 0x08400030
#define SET_FROM_ADDR(X)  \
( (X>>3 & 0x1) <<AD3pin | \
  (X>>2 & 0x1) <<AD2pin | \
  (X>>1 & 0x1) <<AD1pin | \
  (X    & 0x1) <<AD0pin   \
)

static uint8_t CurAddr;

inline void write_address(uint8_t addr){
  if (CurAddr != addr ){
    uint32_t set = SET_FROM_ADDR(addr);
    bcm2835_gpio_set_multi(set);
    bcm2835_gpio_clr_multi(set^ADDR_MASK);
    CurAddr = addr;
  }
}  


#define DATA_MASK 0x07392000
#define SET_FROM_DATA(X) \
( (X>>7      ) <<D7pin | \
  (X>>6 & 0x1) <<D6pin | \
  (X>>5 & 0x1) <<D5pin | \
  (X>>4 & 0x1) <<D4pin | \
  (X>>3 & 0x1) <<D3pin | \
  (X>>2 & 0x1) <<D2pin | \
  (X>>1 & 0x1) <<D1pin | \
  (X    & 0x1) <<D0pin   \
)

inline void write_data(uint8_t data){
  uint32_t set = SET_FROM_DATA(data);
  bcm2835_gpio_set_multi(set);
  bcm2835_gpio_clr_multi(set^DATA_MASK);
}  


#define DEMANGLE_DATA(X)  \
( (X>>D7pin & 0x1) << 7 | \
  (X>>D6pin & 0x1) << 6 | \
  (X>>D5pin & 0x1) << 5 | \
  (X>>D4pin & 0x1) << 4 | \
  (X>>D3pin & 0x1) << 3 | \
  (X>>D2pin & 0x1) << 2 | \
  (X>>D1pin & 0x1) << 1 | \
  (X>>D0pin & 0x1) \
)

// Globals to cache the GPIO LEV and FSEL addresses
static uint32_t *GPIO_LEV_ADDR;
static uint32_t *GPIO_FSEL1_ADDR;
static uint32_t *GPIO_FSEL2_ADDR;

static const uint32_t DATA_FSEL1_MASK =
    BCM2835_GPIO_FSEL_MASK << (D7pin % 10) * 3 |
    BCM2835_GPIO_FSEL_MASK << (D6pin % 10) * 3 |
    BCM2835_GPIO_FSEL_MASK << (D1pin % 10) * 3;
static const uint32_t DATA_FSEL2_MASK =
    BCM2835_GPIO_FSEL_MASK << (D5pin % 10) * 3 |
    BCM2835_GPIO_FSEL_MASK << (D4pin % 10) * 3 |
    BCM2835_GPIO_FSEL_MASK << (D3pin % 10) * 3 |
    BCM2835_GPIO_FSEL_MASK << (D2pin % 10) * 3 |
    BCM2835_GPIO_FSEL_MASK << (D0pin % 10) * 3;

static const uint32_t DATA_FSEL1_OUTP =
    BCM2835_GPIO_FSEL_OUTP << (D7pin % 10) * 3 |
    BCM2835_GPIO_FSEL_OUTP << (D6pin % 10) * 3 |
    BCM2835_GPIO_FSEL_OUTP << (D1pin % 10) * 3;
static const uint32_t DATA_FSEL2_OUTP =
    BCM2835_GPIO_FSEL_OUTP << (D5pin % 10) * 3 |
    BCM2835_GPIO_FSEL_OUTP << (D4pin % 10) * 3 |
    BCM2835_GPIO_FSEL_OUTP << (D3pin % 10) * 3 |
    BCM2835_GPIO_FSEL_OUTP << (D2pin % 10) * 3 |
    BCM2835_GPIO_FSEL_OUTP << (D0pin % 10) * 3;

static const uint32_t DATA_FSEL1_INPT =
    BCM2835_GPIO_FSEL_INPT << (D7pin % 10) * 3 |
    BCM2835_GPIO_FSEL_INPT << (D6pin % 10) * 3 |
    BCM2835_GPIO_FSEL_INPT << (D1pin % 10) * 3;
static const uint32_t DATA_FSEL2_INPT =
    BCM2835_GPIO_FSEL_INPT << (D5pin % 10) * 3 |
    BCM2835_GPIO_FSEL_INPT << (D4pin % 10) * 3 |
    BCM2835_GPIO_FSEL_INPT << (D3pin % 10) * 3 |
    BCM2835_GPIO_FSEL_INPT << (D2pin % 10) * 3 |
    BCM2835_GPIO_FSEL_INPT << (D0pin % 10) * 3;


/*
#include <map>
using namespace std;

struct A{
    static map<int,int> create_map()
        {
          map<int,int> m;
          m[1] = 2;
          m[3] = 4;
          m[5] = 6;
          return m;
        }
    static const map<int,int> myMap;

};

const map<int,int> A:: myMap =  A::create_map();
*/
