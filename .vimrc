set nocompatible              " be iMproved, required
filetype off                  " required
set noswapfile                " disable swaping
set noesckeys                 " disable delay after pressing ESC key

" Next string is not needed if 'filetype plugin indent on' enagled, which it
" is further in this config file.
" Remove it completely if do not experiense any drawbacks.
" filetype plugin on

" custom functions
function! NumberToggle() " can be used to toggle display line num
    if (&relativenumber == 1 && &number == 1)
        set norelativenumber
        set nonumber
    else
        set relativenumber
        set number
    endif
endfunc
function! EnterInsertMode()
    if (&relativenumber == 1)
        set norelativenumber
    endif
endfunc
function! LeaveInsertMode()
    if (&number == 1)
        set relativenumber
    endif
endfunc

" auto commands
autocmd InsertEnter * call EnterInsertMode()
autocmd InsertLeave * call LeaveInsertMode()
autocmd FileType yaml setlocal ts=2 sts=2 sw=2 expandtab

" set the runtime path to include Vundle and initialize
set rtp+=~/.vim/bundle/Vundle.vim
call vundle#begin()
" alternatively, pass a path where Vundle should install plugins
"call vundle#begin('~/some/path/here')

" let Vundle manage Vundle, required
Plugin 'mattn/emmet-vim'
Plugin 'raimondi/delimitmate' " auto completion for quotes, parens, bracks, etc
Plugin 'VundleVim/Vundle.vim'
Plugin 'nanotech/jellybeans.vim'
Plugin 'pangloss/vim-javascript'
Plugin 'taglist.vim'
Plugin 'othree/html5.vim'
Plugin 'hail2u/vim-css3-syntax'
Plugin 'scrooloose/nerdtree'
Plugin 'bling/vim-airline'
Plugin 'vim-airline/vim-airline-themes'
Plugin 'godlygeek/tabular' " :help tabular
Plugin 'scrooloose/syntastic' " syntax checker
" snipmate begins
Plugin 'MarcWeber/vim-addon-mw-utils'
Plugin 'tomtom/tlib_vim'
Plugin 'garbas/vim-snipmate'
Plugin 'honza/vim-snippets'
" snipmate ends
Plugin 'ctrlpvim/ctrlp.vim'
Plugin 'cakebaker/scss-syntax.vim'
Plugin 'freitass/todo.txt-vim'

" All of your Plugins must be added before the following line
call vundle#end()            " required
" To ignore plugin indent changes, instead use:
"filetype plugin on
"
" Brief help
" :PluginList       - lists configured plugins
" :PluginInstall    - installs plugins; append `!` to update or just :PluginUpdate
" :PluginSearch foo - searches for foo; append `!` to refresh local cache
" :PluginClean      - confirms removal of unused plugins; append `!` to auto-approve removal
"
" see :h vundle for more details or wiki for FAQ
" Put your non-Plugin stuff after this line

set fileencodings=utf-8

" Enable syntax highlighting
filetype plugin indent on
syntax on

" Visual wrapping
" Wrapping occurs after characters listed in the "breakat" string option
" (:help breakat). To take indentation into account use breakindent option
" (see :help breakindentopt for details)
" set linebreak

" Spacing
set tabstop=4 " Number of cpaces that a <Tab> in the file counts for.
set shiftwidth=4 " Number of spaces to use for each step of (auto)indent.
set expandtab " Use the appropriate number of spaces to insert a <Tab>
set smarttab " When on, <Tab> in front of a line insert blanks

" various settings
" set textwidth=80 " Maximum width of text that is being inserted
set foldmethod=indent
set colorcolumn+=80
set cursorline " Hihglight current line
set autoindent " copy indent from current line when starting a new line
set incsearch " Search while typingg
set ignorecase " Ignore case in search
set showmatch " When a bracket is inserted, briefly jump to the matching one
set number " Show line nuumbers
set relativenumber " Show relative line numbers ;-)
set hidden  " You can have edited buffers that aren't visible
            " in a window somwhere. Vim doesn't ask for save file when
            " attempting to switch buffers.
set t_Co=256 " Tell Vim I'm using terminal with color support
colorscheme jellybeans

" show hidden characters
set list
set listchars=tab:»-,trail:·,eol:¬

" airline options
set laststatus=2 " Display airline permanently
let g:airline#extensions#tabline#enabled = 1 " Enable the list of buffers
let g:airline#extensions#tabline#fnamemod = ':t' " Show just the filename
let g:airline_powerline_fonts = 1

" key bindings
nnoremap <silent> <F8> :TlistToggle<CR>
nnoremap <silent> <F4> :NERDTreeToggle<CR>
nnoremap <silent> <C-l> :bnext<CR>
nnoremap <silent> <C-h> :bprevious<CR>
nnoremap <silent> <C-n> :call NumberToggle()<CR>

let g:ctrlp_map = '<c-p>'
let g:ctrlp_cmd = 'CtrlP'

" let maplocalleader = '\\'

" Syntastic configuration
set statusline+=%#warningmsg#
set statusline+=%{SyntasticStatuslineFlag()}
set statusline+=%*

let g:syntastic_always_populate_loc_list = 1
let g:syntastic_auto_loc_list = 1
let g:syntastic_check_on_open = 1
let g:syntastic_check_on_wq = 0
let g:syntastic_javascript_checkers = ['jshint']
let g:syntastic_javascript_exec = 'jshint'
let g:syntastic_yaml_checkers = ['yamllint']

" snipMate configuration
let g:snipMate = { 'snippet_version' : 1 }

