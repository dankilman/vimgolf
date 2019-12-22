nnoremap <C-J> :<C-U>call InspectCompareNext()<CR>
nnoremap <C-K> :<C-U>call InspectComparePrevious()<CR>
            
let g:inspectPairs = [
\    ['in0.txt', 'in1.txt'],
\    ['in1.txt', 'in2.txt'],
\    ['in2.txt', 'in3.txt'],
\]
let g:currentInspectPair = 0

function! InspectCompareNext()
    if g:currentInspectPair >= len(g:inspectPairs) - 1
        let g:currentInspectPair = 0
    else
        let g:currentInspectPair += 1
    endif
    call InspectCompare()
endfunction

function! InspectComparePrevious()
    if g:currentInspectPair <= 0
        let g:currentInspectPair = len(g:inspectPairs) - 1
    else
        let g:currentInspectPair -= 1
    endif
    call InspectCompare()
endfunction

function! InspectCompare()
    let currentPair = g:inspectPairs[g:currentInspectPair]
    let topItem = currentPair[0]
    let buttomItem = currentPair[1]
    echo topItem
    echo buttomItem
    return
    windo diffoff
    only
    edit topItem
    belowright split buttomItem
    windo diffthis
endfunction
