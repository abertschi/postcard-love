#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <unistd.h>
#include <string.h>
#include <stdbool.h>

#include "mm.h"
#include "memlib.h"

team_t team = {

  "bean",

  ""

  ""

  "",

  ""
};

/* single word (4) or double word (8) alignment */
#define ALIGNMENT 8

#define MIN(a,b) (((a)<(b))?(a):(b))
#define MAX(a,b) (((a)>(b))?(a):(b))

/* rounds up to the nearest multiple of ALIGNMENT */
#define ALIGN(size) (((size) + (ALIGNMENT-1)) & ~0x7)

#define SIZE_T_SIZE (ALIGN(sizeof(size_t)))

#define UNMARK_BLOCK(block) (block & ~0x1)
#define MARK_BLOCK(block) (block | 0x1)
#define IS_BLOCK_MARKED(block) !!(block & 0x1)
#define GET_BLOCK_SIZE(block) (block & ~0x7)
#define SET_BLOCK_SIZE(block, size) (ALIGN(size) | (block & 0x1))

#define ADD_BYTES_TO_PTR(p, bytes) ((size_t *) ((char *) p + bytes))
#define HI_FOOT  ((size_t *) ((char *) mem_heap_hi() - SIZE_T_SIZE + 1))
#define LOW_HEAD ((size_t *) mem_heap_low())

#define GET_FOOT_WITH_HEAD(head)                                \
  (ADD_BYTES_TO_PTR(head, GET_BLOCK_SIZE(*head) + SIZE_T_SIZE))

#define GET_HEAD_WITH_FOOT(foot)                                        \
  (ADD_BYTES_TO_PTR(foot, -( GET_BLOCK_SIZE(*foot) + SIZE_T_SIZE)))

#define GET_NEXT_HEAD(head)                                             \
  (ADD_BYTES_TO_PTR(head, GET_BLOCK_SIZE(*head) + 2 * SIZE_T_SIZE))

#define GET_PREVIOUS_FOOT(foot)                                         \
  (ADD_BYTES_TO_PTR(foot, -(GET_BLOCK_SIZE(*foot) + 2 * SIZE_T_SIZE)))

// enable this to verify consistency
/* #define DEBUG */
// 
#ifdef DEBUG
#define D 
#else
#define D for(;0;)
#endif

static size_t* last_modified_head = NULL;


static void mm_check(int p)
{
  if (!mem_heap_lo()) return;

  size_t * head = mem_heap_lo();
  size_t * foot = GET_FOOT_WITH_HEAD(head);

  while(1)
  {
    bool size_good = GET_BLOCK_SIZE(*head) == GET_BLOCK_SIZE(*foot);
    bool mark_good = IS_BLOCK_MARKED(*head) == IS_BLOCK_MARKED(*foot);

    if (!size_good || !mark_good)
    {
      assert(false);
    }
    head = GET_NEXT_HEAD(head);
    foot =  GET_FOOT_WITH_HEAD(head);

    if (foot >= HI_FOOT)
    {
      break;
    }
  }
}

static int allocate_block(size_t size, size_t** head)
{
  int newsize = ALIGN(size + SIZE_T_SIZE * 2);
  void *mem_p = mem_sbrk(newsize);

  if (mem_p == (void *) -1)
    return 0; // ran out of mem

  *head = (size_t *) mem_p;
  **head = ALIGN(size);
  **head = UNMARK_BLOCK(**head);

  size_t *foot = GET_FOOT_WITH_HEAD(*head);
  *foot = ALIGN(size);
  *foot = UNMARK_BLOCK(*foot);

  // asserts
  D assert(GET_HEAD_WITH_FOOT(foot) == *head          \
           && GET_FOOT_WITH_HEAD(*head) == foot);

  D assert(newsize == (2 * SIZE_T_SIZE + ALIGN(size)) && "matching sizing");
  return 1;
}

/* 
 * mm_init - initialize the malloc package.
 */
int mm_init(void)
{
  last_modified_head = mem_heap_lo();
  return 0;
}

/*
 * if block at head has padding that can be recycled,
 * rearrange head/foot so that padding becomes
 * a new block
 * to improve:
 *  - unite block when more blocks are free later on
 *
 */
static void recycle_padding(size_t *head, size_t size)
{
  size_t block_size = GET_BLOCK_SIZE(*head); // aligned
  long unused = block_size - ALIGN(size) - 2 * SIZE_T_SIZE;
  unused = (unused < 0) ? 0 : unused;
  if (unused > 0)
  {
    size_t * obsolte_foot = GET_FOOT_WITH_HEAD(head);
    *head = SET_BLOCK_SIZE(*head, ALIGN(size));
    *head = MARK_BLOCK(*head);

    size_t *new_foot = GET_FOOT_WITH_HEAD(head);
    *new_foot = SET_BLOCK_SIZE(*new_foot, ALIGN(size));
    *new_foot = MARK_BLOCK(*new_foot);

    size_t *unused_head = ADD_BYTES_TO_PTR(new_foot, SIZE_T_SIZE);
    *unused_head = SET_BLOCK_SIZE(*unused_head, unused);
    *obsolte_foot = SET_BLOCK_SIZE(*obsolte_foot, unused);
    *unused_head = UNMARK_BLOCK(*unused_head);
    *obsolte_foot = UNMARK_BLOCK(*obsolte_foot);

    last_modified_head = unused_head;


    D assert(GET_HEAD_WITH_FOOT(obsolte_foot) == unused_head
             
             && GET_FOOT_WITH_HEAD(unused_head) == obsolte_foot);

    D assert(GET_HEAD_WITH_FOOT(new_foot) == head
             && GET_FOOT_WITH_HEAD(head) == new_foot);

    // no performance impact
    /* *unused_head = MARK_BLOCK(*unused_head); */
    /* *obsolte_foot = MARK_BLOCK(*obsolte_foot); */

    /* mm_free(ADD_BYTES_TO_PTR(unused_head, SIZE_T_SIZE)); */
  }
}

/* 
 * mm_malloc - Allocate a block by incrementing the brk pointer.
 *     Always allocate a block whose size is a multiple of the alignment.
 */
void *mm_malloc(size_t size)
{
  D mm_check(0);
  size_t *head = last_modified_head;
  bool success = 0;

  size_t * max_heap = (size_t *) mem_heap_hi();
  for(;;)
  {
    if (head >= max_heap)
    {
      break;
    }
    size_t bsize = GET_BLOCK_SIZE(*head);
    if (size <= bsize && !IS_BLOCK_MARKED(*head))
    {
      success = 1;
      break;
    }
    size_t s = 2 * SIZE_T_SIZE + bsize;
    head = ADD_BYTES_TO_PTR(head, s);
  }
  if (success)
  {
    // a block was found which is at least required size
    // try to reuse padding
    size_t *foot = GET_FOOT_WITH_HEAD(head);
    *head = MARK_BLOCK(*head);
    *foot = MARK_BLOCK(*foot);
    recycle_padding(head, size);
  }
  else
  {
    size_t s = size; // MAX(size, MIN_ALLOC_SIZE);
    if (!allocate_block(s, &head)) return NULL;
    size_t *foot = GET_FOOT_WITH_HEAD(head);
    *head = SET_BLOCK_SIZE(*head, s); // store lenght
    *foot = SET_BLOCK_SIZE(*foot, s);
    *head = MARK_BLOCK(*head);
    *foot = MARK_BLOCK(*foot);
    // recycle_padding(head, size);    
    
  }
  //last_modified_head = head;
  return (void *) ADD_BYTES_TO_PTR(head, SIZE_T_SIZE);
}

/*
 * mm_free - Freeing a block does nothing.
 */
void mm_free(void *ptr)
{
  D mm_check(1);

  size_t *head = ADD_BYTES_TO_PTR((size_t*) ptr, -SIZE_T_SIZE);
  size_t *foot = GET_FOOT_WITH_HEAD(head);

  bool next_head_free = foot < HI_FOOT
      && !IS_BLOCK_MARKED(*GET_NEXT_HEAD(head));

  bool prev_foot_free = head > (size_t *) mem_heap_lo()
      && !IS_BLOCK_MARKED(* GET_PREVIOUS_FOOT(foot));

  // case 1: block to free is between 2 allocated blocks
  if (!next_head_free && !prev_foot_free)
  {
    *head = UNMARK_BLOCK(*head);
    *foot = UNMARK_BLOCK(*foot);
    last_modified_head = head;
    D mm_check(10);

  }
  // case 2: next block is free but previous isnt
  else if (next_head_free && !prev_foot_free)
  {
    foot = GET_FOOT_WITH_HEAD(GET_NEXT_HEAD(head));
    *head = UNMARK_BLOCK(*head);
    *foot = UNMARK_BLOCK(*foot);

    size_t size = GET_BLOCK_SIZE(*head)
        + GET_BLOCK_SIZE(*foot)
        + 2 * SIZE_T_SIZE;

    *head = SET_BLOCK_SIZE(*head, size);
    *foot = SET_BLOCK_SIZE(*foot, size);
    last_modified_head = head;
    D mm_check(11);
  }
  // case 3: previous block free but next isnt
  else if (!next_head_free && prev_foot_free)
  {
    head = GET_HEAD_WITH_FOOT(GET_PREVIOUS_FOOT(foot));
    *head = UNMARK_BLOCK(*head);
    *foot = UNMARK_BLOCK(*foot);

    size_t size = GET_BLOCK_SIZE(*head)
        + 2 * SIZE_T_SIZE
        + GET_BLOCK_SIZE(*foot);

    *head = SET_BLOCK_SIZE(*head, size);
    *foot = SET_BLOCK_SIZE(*foot, size);
    last_modified_head = head;
    D mm_check(12);
  }
  // case head and foot are free
  else
  {
    size_t *h = GET_HEAD_WITH_FOOT(GET_PREVIOUS_FOOT(foot));
    size_t *f = GET_FOOT_WITH_HEAD(GET_NEXT_HEAD(head));

    size_t size = GET_BLOCK_SIZE(*h)
        + GET_BLOCK_SIZE(*GET_NEXT_HEAD(h))
        + GET_BLOCK_SIZE(*f)
        + 4 * SIZE_T_SIZE;

    *h = SET_BLOCK_SIZE(*h, size);
    *f = SET_BLOCK_SIZE(*f, size);

    *h = UNMARK_BLOCK(*h);
    *f = UNMARK_BLOCK(*f);
    last_modified_head = h;
    D mm_check(13);
  }
}

/*
 * mm_realloc - Implemented simply in terms of mm_malloc and mm_free
 */
void *mm_realloc(void *ptr, size_t size)
{
  if (!size)
  {
    mm_free(ptr);
    return ptr;
  }
  if (!ptr)
    return mm_malloc(size);

  size_t *head = ADD_BYTES_TO_PTR((size_t *) ptr, -SIZE_T_SIZE);
  size_t old_size = GET_BLOCK_SIZE(*head);
  if (size <= old_size)
  {
    // recycle_padding(ptr, size);
    return ptr;
  }
  size_t *new_ptr = (size_t *) mm_malloc(size);
  memcpy((void *) new_ptr, ptr, old_size);
  mm_free(ptr);
  return new_ptr;
}
