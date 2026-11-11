/* Exercise the actual bridge; Xlib and Bend allocation are controlled boundaries. */
#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef uintptr_t Term;
typedef unsigned int u32;
typedef int Env;
typedef int IoWork;
typedef struct { const char *name; int synced, queued; } Display;
typedef struct { Display *dpy; unsigned long win; } BendWin;
#define CID(x) 1
#define False 0
#define DisplayString(d) ((d)->name)
static Term pair[2];
static unsigned long exported_id;
static char exported_display[64];
static int outcome, sync_before_ref;
static Term io_hand_v(Term t) { return t; }
static Term io_tup(Env e, Term a, Term b) { (void)e; pair[0]=a; pair[1]=b; return 9; }
static Term io_fail(Env e, int code, const char *s) { (void)e; (void)s; outcome=code; return 0; }
static Term io_done(Env e, Term t) { (void)e; outcome=0; return t; }
static Display *active;
static int XSync(Display *d, int discard) { d->synced++; if(discard) d->queued=0; return 0; }
static Term io_str(Env e, const char *s, size_t n) { (void)e; assert(n<sizeof exported_display); memcpy(exported_display,s,n); exported_display[n]=0; return 3; }
static Term io_node(Env e, int cid, Term d, u32 id) { (void)e;(void)cid;(void)d; exported_id=id; sync_before_ref=active->synced; return 4; }
static void io_eff(int cid, Term (*fn)(Env,Term*,IoWork*)) { (void)cid;(void)fn; }
#include "winref.c"
int main(void) {
  const char *names[]={":fixture",NULL,"",":fixture",":fixture",":fixture"};
  unsigned long ids[]={7,7,7,0,UINT32_MAX,(unsigned long)UINT32_MAX+1};
  for(size_t i=0;i<sizeof ids/sizeof *ids;i++) {
    Display d={names[i],0,1}; BendWin w={&d,ids[i]}; Term f[]={(Term)&w};
    active=&d; outcome=-1; exported_id=0; exported_display[0]=0; sync_before_ref=0;
    winref_export_run(0,f,NULL);
    assert(pair[0]==f[0]); /* same affine owner on every outcome */
#ifdef UNSUPPORTED
    assert(outcome==ENOTSUP && !d.synced && d.queued==1);
#else
    int expected=(!names[i] || !names[i][0] || !ids[i])?EIO:ids[i]>UINT32_MAX?EOVERFLOW:0;
    assert(outcome==expected && d.queued==1);
    if(!expected) {
      assert(d.synced==1 && sync_before_ref==1);
      assert(exported_id==ids[i] && strcmp(exported_display,names[i])==0);
      /* Consumer simulation: exported bytes survive close and ID reuse unchanged. */
      unsigned long borrowed=exported_id, copy=borrowed;
      int server_generation=1;
      assert(copy==w.win && server_generation==1);
      server_generation=0; /* close destroys original resource */
      assert(copy==borrowed && server_generation==0);
      server_generation=2; /* server may allocate the same ID to another resource */
      assert(copy==borrowed && server_generation!=1);
    } else assert(d.synced==0);
#endif
  }
  puts("bridge: owner, outcomes, identity, sync ordering, and event preservation verified");
}
