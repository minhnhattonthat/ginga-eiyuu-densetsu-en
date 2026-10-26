; engine.asm: English text engine (asar 1.91, applied by tools/build.py to every English build).
; Facts: docs/re/text.md (renderer, control codes), docs/re/engine.md (this patch, hook list).
;
; 1. VWF: the 12px fixed-pitch glyph drawer ($07:9BBF-9D91) is replaced. Glyph codes < $100 come from the English
;    font in bank $0F (32 bytes each, same TL/TR/BL/BR 1bpp layout as the JP font, one advance byte each); codes
;    >= $100 (D0/D1 xx) still draw the JP kanji at 12 px. $1167 stays "canvas tile column of the pen" and $111E
;    becomes "pen pixel offset in that tile" (0-7); every place that resets a line sets both to 0, as before.
; 2. F8 lo hi bank = far jump: the text pointer continues at a 24-bit address. Lets main/sub strings and names live
;    in any bank (the tables only hold 16-bit pointers into bank $05 / $02).
; 3. Name slots: $00:F46B (copy a length-prefixed name into a 16-byte RAM slot) writes `F8 <name chars>` instead,
;    so names have no length cap.

lorom

!buf = $1127            ; 3 tile columns x 16 rows; column c row r at !buf+16*c+r (rows 0-7 top tile, 8-15 bottom)
!w = $1157              ; advance of the glyph being drawn
!sh = $1158             ; pen offset in the column (16-bit store, high byte 0)
!row = $115A            ; 16-bit
!spill = $115C          ; 16-bit; high byte = bits shifted into the third column
!n = $115E              ; tiles touched (16-bit)
!vram = $1160           ; 16-bit word address of the top tile being queued
!stride = $1162         ; 16-bit: words from a top tile to the tile below it = (canvas width in tiles) * 8
!k = $1164              ; 16-bit column counter
!src = $C1              ; long pointer to the glyph (direct page $C1-$C3)

; ---- hooks (each asserts the original bytes) ----
assert read1($079BBF) == $AD && read1($079BC0) == $BC, "VWF hook site moved"
org $079BBF
        jml vwf_draw            ; $BB/$BC = glyph index (16-bit), M8 X16

assert read1($079A39) == $AD && read1($079A3C) == $F0, "FF hook site moved"
org $079A39
        jml ff_code             ; A = control byte FF or F8-FB
        nop

assert read1($00F46B) == $CA && read1($00F46C) == $86, "name copy hook site moved"
org $00F46B
        jml name_slot           ; X = RAM slot, [$B8] = length-prefixed name

; $00:F4D6 copies the side name (同盟軍/帝国軍, 8 bytes inside bank $00 code) into slot $1F60: point it at
; $0F:8E00 / $0F:8E80 instead, where tools/build.py writes the English (SIDE_FAR).
assert read2($00F4D7) == $F4EE && read2($00F4DE) == $F4F6 && read1($00F4E3) == $00, "side name hook moved"
org $00F4D7
        dw $8E00
org $00F4DE
        dw $8E80
org $00F4E3
        db $0F

; $00:F538 writes a number (losses in m134 etc.) as digits into slot $1F40 for {sub0:03}: JP digit codes start at $89,
; English ones at '0' ($30). Glyph $89 is past the English font: the VWF drew garbage and the result scenes crashed.
assert read1($00F556) == $69 && read1($00F557) == $89, "number digit base moved"
org $00F557
        db $30

; 4. Command help label (slot 7 of the button drawer $00:A6DD: A = gfx id, X = slot 0-7) is 6x2 tiles at map x 23
;    instead of 3x2 at x 26, so English words fit; its blocks (0E_0F-18, 0E_27-31) hold 12 tiles (tools/gfxtext.py).
;    Tiles $AA-$B5 (BG3): $B0-$B5 were past the last slot, unused by the BG3 map on the command screens.
assert read1($00A705) == $A9 && read1($00A706) == $03 && read1($00A709) == $A9, "label clear hook moved"
org $00A705
        jml label_clear         ; M8 X16, $46 = slot; was LDA #3 STA $D1 LDA #2 STA $D2
assert read2($00A752) == $DAA2 && read1($00A75B) == $A9 && read1($00A762) == $D2, "label draw hook moved"
org $00A752
        jml label_draw          ; was: $CC = $00:11DA (template from $00:94E3), $D1 = 3, $D2 = 2
assert read2($00A7C6) == $111A, "label position moved"
org $00A7C6
        dw $1117                ; slot 7 map position: x 26 -> 23, y 17

org $0F8000
vwf_draw:
        php
        rep #$20
        lda $BB
        cmp.w #$0100
        bcs .jp
        tax
        asl #5
        clc
        adc.w #en_font&$FFFF
        sta !src
        sep #$20
        lda.b #en_font>>16
        sta !src+2
        lda.l en_width,x
        sta !w
        bra .go
.jp:    asl #5                  ; JP font $06:8000 + 32 * index
        clc
        adc.w #$8000
        sta !src
        sep #$20
        lda.b #$06
        sta !src+2
        lda.b #12
        sta !w
.go:    stz !sh+1
        lda $111E
        sta !sh
        bne .rows
        rep #$20                ; pen at a column start: nothing drawn there yet, start from blank columns
        ldx.w #46
-       stz !buf,x
        dex
        dex
        bpl -
.rows:  rep #$20
        stz !row
.row:   lda !row                ; Y = glyph offset of the row's left byte: r + (r & 8)
        and.w #$0008
        clc
        adc !row
        tay
        sep #$20
        lda [!src],y
        xba
        iny #8                  ; (not TYA/ADC/TAY: with X16 that TAY copies B into Y's high byte)
        lda [!src],y            ; C = left:right
        rep #$20
        stz !spill
        ldx !sh
        beq .put
-       lsr
        ror !spill
        dex
        bne -
.put:   ldx !row
        sep #$20
        ora !buf+16,x
        sta !buf+16,x
        xba
        ora !buf,x
        sta !buf,x
        lda !spill+1
        ora !buf+32,x
        sta !buf+32,x
        rep #$20
        inc !row
        lda !row
        cmp.w #16
        bne .row

        ; tiles touched: ((sh + w - 1) >> 3) + 1
        lda !w
        and.w #$00FF
        clc
        adc !sh
        dec
        lsr #3
        inc
        sta !n
        ; top-left tile word address: $6000 + 8 * ($1118 + $1167); tile below: + 8 * ($117F - 2)
        lda $1167
        and.w #$00FF
        clc
        adc $1118
        asl #3
        clc
        adc.w #$6000
        sta !vram
        lda $117F
        and.w #$00FF
        dec
        dec
        asl #3
        sta !stride
        sep #$20
        lda.b #$FF              ; plane 1 byte, as the original ($116A set = 0)
        sta $116B
        lda $116A
        beq +
        stz $116B
+       jsl $008B60             ; $BD = free DMA queue block
        ldy.w #$0000
        ldx.w #$0000            ; X = buffer offset of the column (16 * k)
        rep #$20
        stz !k
.tile:  lda !vram
        jsr queue_tile          ; top half: rows 0-7
        txa
        clc
        adc.w #8
        tax
        lda !vram
        clc
        adc !stride
        jsr queue_tile          ; bottom half: rows 8-15
        txa
        clc
        adc.w #8
        tax
        lda !vram
        clc
        adc.w #8
        sta !vram
        inc !k
        lda !k
        cmp !n
        bne .tile
        sep #$20
        lda.b #$FF
        sta ($BD),y

        ; advance the pen: t = sh + w; $1167 += t >> 3; $111E = t & 7; drop the finished columns
        lda !w
        clc
        adc !sh
        pha
        and.b #$07
        sta $111E
        pla
        lsr #3
        beq .done
        pha
        clc
        adc $1167
        sta $1167
        pla
        ldx.w #0
        cmp.b #1                ; 8-bit compare; REP leaves Z alone
        rep #$20
        bne .two
-       lda !buf+16,x           ; one column: c0 <- c1, c1 <- c2, c2 <- 0
        sta !buf,x
        lda !buf+32,x
        sta !buf+16,x
        stz !buf+32,x
        inx
        inx
        cpx.w #16
        bne -
        bra .done
.two:
-       lda !buf+32,x           ; two columns: c0 <- c2, c1 <- 0, c2 <- 0
        sta !buf,x
        stz !buf+16,x
        stz !buf+32,x
        inx
        inx
        cpx.w #16
        bne -
.done:  plp
        rtl

; queue one 2bpp tile: A (16-bit) = VRAM word address, X = buffer offset of its 8 plane-0 rows, Y = queue index.
; Entry: $80, addr lo, addr hi, $08 (words), then 8 x (plane 0, plane 1). Returns M16, X kept, Y advanced.
queue_tile:
        sep #$20
        xba
        pha
        lda.b #$80
        sta ($BD),y
        iny
        xba
        sta ($BD),y
        iny
        pla
        sta ($BD),y
        iny
        lda.b #$08
        sta ($BD),y
        iny
        phx
        lda.b #$08
        sta !spill
-       lda !buf,x
        sta ($BD),y
        iny
        lda $116B
        sta ($BD),y
        iny
        inx
        dec !spill
        bne -
        plx
        rep #$20
        rts

; FF / F8-FB reach $07:9A39. F8 lo hi bank: continue reading at that address (the substring return pointer and
; flag $117E are left alone, so an FF after a jumped-to name still returns from the substring).
ff_code:
        cmp.b #$F8
        beq .far
        lda $117E
        beq +
        jml $079A3E
+       jml $079A56
.far:   jsl $079DE3
        pha
        jsl $079DE3
        pha
        jsl $079DE3
        sta $1115
        pla
        sta $1114
        pla
        sta $1113
        jml $07995D

; X = RAM slot, [$B8] = name (length byte, chars, FF). Writes F8 + address of the chars into the slot.
name_slot:
        php
        sep #$20
        lda.b #$F8
        sta.l $000000,x
        rep #$20
        lda $B8
        inc
        sta.l $000001,x
        sep #$20
        lda $BA
        sta.l $000003,x
        plp
        rtl

label_clear:                    ; M8 X16
        lda #$03
        ldx $46
        cpx.w #$0006            ; slot 6 (x 21, never drawn) clears 2 columns: x 23 is the label's (SYS bar clears
        bne +                   ; slots 3-6 after drawing the label)
        lda #$02
+       cpx.w #$0007
        bne +
        lda #$06
+       sta $D1
        lda #$02
        sta $D2
        jml $00A70D

label_draw:                     ; M8 X16
        ldx $46
        cpx.w #$0007
        beq +
        ldx.w #$11DA
        stx $CC
        lda #$00
        sta $CE
        lda #$03
        bra ++
+       ldx.w #label_map
        stx $CC
        lda.b #label_map>>16
        sta $CE
        lda #$06
++      sta $D1
        lda #$02
        sta $D2
        jml $00A763

label_map:                      ; 6x2 map entries for tiles $AA-$B5, palette 2 (as $00:94E3 builds them)
        dw $08AA, $08AB, $08AC, $08AD, $08AE, $08AF
        dw $08B0, $08B1, $08B2, $08B3, $08B4, $08B5

assert pc() <= $0F8E00          ; $0F:8E00-8EFF: side names (written by tools/build.py)
org $0F8F00
en_width:
        incbin "../build/gen/en_width.bin"
assert pc() <= $0F9000
org $0F9000
en_font:
        incbin "../build/gen/en_font.bin"
assert pc() <= $0FB000
