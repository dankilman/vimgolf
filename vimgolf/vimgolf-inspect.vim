nnoremap <C-J> :<C-U>call InspectCompareNext()<CR>
nnoremap <C-K> :<C-U>call InspectComparePrevious()<CR>
            
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
    let l:currentPair = g:inspectPairs[g:currentInspectPair]
    let l:topItem = currentPair[0]
    let l:bottomItem = currentPair[1]
    execute "windo diffoff"
    execute "only"
    execute "edit " . l:topItem
    execute "belowright split " . l:bottomItem
    execute "windo diffthis"
endfunction
